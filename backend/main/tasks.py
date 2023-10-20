from datetime import timedelta, date

from django.core.mail import send_mail
from django.db.models import QuerySet
from django.utils import timezone
from django.conf import settings
from django_q.tasks import Task
import pandas as pd
import tomotopy as tp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from tomotopy.utils import Corpus
from numpy import argmax

from main.helpers import construct_statistics, format_statistics
from main.models import *


def process_report(report: Report):
    """
    This function processes the report and updates them.

    Args:
        report (Report): The report to process.
    """

    # Check if the report still exists.
    if not Report.objects.filter(id=report.id).exists():
        return

    report.datetime_analysis_started = timezone.now()
    report.save()

    patents = report.get_patents()
    patent_count = patents.count()

    if not settings.DEBUG and patent_count > settings.MAX_PATENTS_PER_REPORT:
        report.results = {
            "error": f"Too many patents ({patent_count}) to process "
            "please narrow down your search. The maximum number of "
            f"patents the server will process is {settings.MAX_PATENTS_PER_REPORT}."
        }

        raise ValueError("Too many patents to process, please narrow down your search.")

    if patent_count == 0:
        report.results = {"info": "No patents found."}
        return

    # Need to filter again because distinct + annotate is not supported by Django.
    patent_ids = list(patents.values_list("id", flat=True))
    report.patent_ids = patent_ids
    report.save()
    patents = Patent.objects.filter(id__in=patent_ids)

    local_network_ids = list(
        PatentCitation.objects.filter(
            citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids
        ).values_list("id", flat=True)
    )

    _create_excel(report, patents)

    report.results = {
        "patents_count": len(patents),
        "statistics": _calculate_statistics(patents),
        "timeseries": {
            "applications_per_year": Patent.applications_per_year(patents),
            "granted_per_year": Patent.granted_patents_per_year(patents),
            "granted_per_type_year": Patent.granted_patents_per_type_year(patents),
            "granted_per_office_per_year": Patent.granted_patents_per_office_year(
                patents
            ),
            "pct_protected_per_year": Patent.pct_protected_patents_per_year(patents),
            "granted_per_cpc_year": Patent.granted_patents_per_cpc_year(patents),
            "citations_made_per_year": Patent.citations_made_per_year(patents),
            "citations_received_per_year": Patent.citations_received_per_year(patents),
        },
        "entity": {
            "patent": {
                "pct": Patent.pct_distribution(patents),
                "type": Patent.types(patents),
                "office": Patent.offices(patents),
            },
            "inventor": {
                "top10": Patent.top_10_inventors(patents),
                "locations": Patent.inventor_locations(patents),
            },
            "assignees": {
                "top10": Patent.top_10_assignees(patents),
                "type": Patent.assignee_type(patents),
                "locations": Patent.assignee_locations(patents),
            },
            "cpc": {
                "section": Patent.cpc_sections(patents),
                "top5_classes": Patent.top_5_cpc_classes(patents),
                "top5_subclasses": Patent.top_5_cpc_subclasses(patents),
                "top5_groups": Patent.top_5_cpc_groups(patents),
            },
        },
        "topic_modeling": _execute_topic_analysis(patents, patent_ids),
        "citations": {
            "graph": PatentCitation.local_network_graph(local_network_ids),
            "most_cited_local": PatentCitation.most_cited_patents_local(
                local_network_ids
            ),
            "most_cited_global": PatentCitation.most_cited_patents_global(patent_ids),
        },
    }


def topic_analysis(
    report: Report,
    method: str = "LDA",
    n_topics: int = 10,
    n_words: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
    rm_top: int | None = 20,
    max_df: float | None = 0.8,
):
    """
    Executes topic analysis and sets the results to the report.

    Args:
        report (Report): The report to execute the topic analysis for.
        method (str, optional): The topic analysis method that will be used. Defaults to "LDA".
        n_topics (int, optional): The numbers of topics that will be generated. Defaults to 10.
        n_words (int, optional): The number of words per each topic. Defaults to 10.
        start_date (str | None, optional): The start date used for cagr calculation. Defaults to None.
        end_date (str | None, optional): The end date used for cagr calculation. Defaults to None.
        rm_top (int | None, optional): The number of most frequent words to be removed (only works for LDA). Defaults to 20.
        max_df (float | None, optional): The maximum document frequency for the tfidf vectorizer (only works for NMF). Defaults to 0.8.
    """

    # Check if the report still exists.
    if not Report.objects.filter(id=report.id).exists():
        return

    results = report.results
    topic_results = results.get("topic_modeling", None)

    # First analysis must be executed
    if topic_results is None:
        return

    # Check if the topic analysis was already executed with the same parameters.
    if (
        method == topic_results["method"]
        and n_topics == topic_results["n_topics"]
        and n_words == topic_results["n_words"]
        and start_date == topic_results["start_date"]
        and end_date == topic_results["end_date"]
        and rm_top == topic_results["rm_top"]
        and max_df == topic_results["max_df"]
    ):
        return

    report.datetime_analysis_started = timezone.now()
    report.save()
    patents = report.get_patents()
    patent_ids = list(patents.values_list("id", flat=True))

    results["topic_modeling"] = _execute_topic_analysis(
        patents,
        patent_ids,
        method,
        n_topics,
        n_words,
        start_date,
        end_date,
        rm_top,
        max_df,
    )

    report.results = results


def execution_hook(task: Task):
    """
    This function is called when a task is executed to update the corresponding report with meta fields.

    Args:
        task (Task): The task that was executed.
    """

    report = task.args[0]

    # Check if the report still exists.
    if not Report.objects.filter(id=report.id).exists():
        return

    report.executed_successfully = task.success

    # Add error message if the task failed but no error message was provided.
    if not report.executed_successfully and (
        report.results is None or report.results.get("error", None) is None
    ):
        report.results = {
            "error": "An unexpected error occurred while processing the report."
        }

    report.status = "idle"
    report.datetime_analysis_ended = timezone.now()
    report.save()

    if report.user.wants_emails and settings.EMAIL_HOST_USER:
        filter_string = "Report Filters:\n"
        for filter, value in report.filters.items():
            filter_string += f"* {filter}: {value}\n"

        mail_url = (
            "http://" if settings.DEBUG else "https://"
        ) + f"{settings.FRONT_END_DOMAIN}/report/{report.id}"

        send_mail(
            subject="PatentAnalyzer: Your report is ready!",
            message=f"Your report with the following filters is ready! "
            + f"Visit PatentAnalyzer ({mail_url}) to view it. \n\n{filter_string}\n\n",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[report.user.email],
        )


def _create_excel(report: Report, patents: QuerySet = None):
    """
    This function creates the excel file for the report and stores it in the database.

    Args:
        report (Report): The report to create the excel file for.
        patents (QuerySet): The patents to include in the excel file if they are already fetched.
    """

    patents = patents if patents is not None else report.get_patents()

    df = pd.DataFrame(Patent.fetch_representation(patents).values())
    if not os.path.exists(os.path.dirname(report.excel_file)):
        os.makedirs(os.path.dirname(report.excel_file))
    df.to_excel(report.excel_file, index=False)
    report.save()


def _calculate_statistics(patents: QuerySet):
    """
    This function calculates the statistics for the given patents.

    Args:
        patents (QuerySet): The patents to calculate the statistics for.
    """

    statistics = {}
    for field in [
        "claims_count",
        "figures_count",
        "sheets_count",
        "years_to_get_granted",
        "title_word_count_without_processing",
        "title_word_count_with_processing",
        "abstract_word_count_without_processing",
        "abstract_word_count_with_processing",
        "cpc_groups_count",
        "assignee_count",
        "inventor_count",
        "incoming_citations_count",
        "outgoing_citations_count",
    ]:
        statistics.update(construct_statistics(field))

    return format_statistics(patents.aggregate(**statistics))


def _execute_topic_analysis(
    patents: QuerySet,
    patent_ids: List[int],
    method: str = "LDA",
    n_topics: int = 10,
    n_words: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
    rm_top: int | None = 20,
    max_df: float | None = 0.8,
) -> Dict:
    """
    This function executes the topic modeling for the given report.

    Args:
        patents (Iterable[Patent]): The patents to execute the topic modeling for.
        patent_ids (List[int]): The ids of the patents, passed for performance reasons
        (e.g when they are already fetched)
        method (str, optional): The topic analysis method. Defaults to "LDA".
        n_topics (int, optional): The topics to be generated. Defaults to 10.
        n_words (int, optional): The words per topic to be displayed. Defaults to 10.
        start_date (str | None, optional): The start date used for CAGR classification. Defaults to None.
        end_date (str | None, optional):  The end date used for CAGR classification. Defaults to None.
        rm_top (int | None, optional): The number of most frequent words to be removed (only works for LDA). Defaults to 20.
        max_df (float | None, optional): The maximum document frequency for the tfidf vectorizer (only works for NMF). Defaults to 0.8.

    Returns:
        Dict: The results of the topic analysis (words, weights, ratio
        and cagr per topic) and the coherence score
    """

    if end_date is None:
        end_date = patents.aggregate(max_date=Max("granted_date"))[
            "max_date"
        ] - timedelta(days=365 * 3)
    else:
        end_date = date.fromisoformat(end_date)

    if start_date is None:
        start_date = end_date - timedelta(days=365 * 5)
    else:
        start_date = date.fromisoformat(start_date)

    arguments = [patents, patent_ids, n_topics, n_words]
    results, patents_per_topic = (
        _topic_analysis_nmf(*arguments, max_df)
        if method == "NMF"
        else _topic_analysis_lda(*arguments, rm_top)
    )

    # Calculate the ratio and ratio cagr of patents per topic
    years_diff = (end_date - start_date).days / 365
    (
        total_patents_in_start_year,
        total_patents_in_end_year,
    ) = Patent.patent_count_in_2_dates(patents, start_date, end_date)

    for i, patents in enumerate(patents_per_topic):
        results["topics"][i]["count"] = len(patents)
        patents = Patent.objects.filter(id__in=patents)

        (
            patents_in_start_year,
            patents_in_end_year,
        ) = Patent.patent_count_in_2_dates(patents, start_date, end_date)

        # Add 1 to avoid division by zero
        patent_share_in_start_year = patents_in_start_year / (
            total_patents_in_start_year + 1
        )
        patent_share_in_end_year = patents_in_end_year / (total_patents_in_end_year + 1)

        results["topics"][i]["ratio"] = len(patents) / len(patent_ids)
        results["topics"][i]["cagr"] = (
            patent_share_in_end_year / (patent_share_in_start_year + 1e-9)
        ) ** (1 / years_diff) - 1

    results["method"] = method
    results["n_topics"] = n_topics
    results["n_words"] = n_words
    results["start_date"] = start_date
    results["end_date"] = end_date
    results["rm_top"] = rm_top
    results["max_df"] = max_df

    return results


def _topic_analysis_lda(
    patents: QuerySet, patent_ids: List[int], n_topics: int, n_words: int, rm_top: int
) -> Tuple[Dict, List[List[int]]]:
    """
    This function executes topic modeling for the given patents using LDA.

    Args:
        patents (QuerySet): The patents to execute the topic modeling for.
        patent_ids (List[int]): The ids of the patents, passed for performance reasons.
        n_topics (int): The number of topics to be generated.
        n_words (int): The number of words per topic to be displayed.
        rm_top (int): The number of most frequent words to be removed.

    Returns:
        Tuple[Dict, List[List[int]]]: The results of the topic analysis
        (words and weights per topic) and the patents per topic.
    """

    docs = patents.annotate(
        doc=Func(
            Concat(
                "title_processed",
                Value(" "),
                "abstract_processed",
                output_field=fields.TextField(),
            ),
            Value(" "),
            function="string_to_array",
            output_field=ArrayField(models.CharField()),
        )
    ).values_list("doc", flat=True)

    lda = tp.LDAModel(k=n_topics, rm_top=rm_top)
    corpus = Corpus()
    for doc in docs:
        corpus.add_doc(doc)
    lda.add_corpus(corpus)
    lda.train(iter=3000)

    patents_per_topic = [[] for _ in range(lda.k)]
    results = _format_topic_analysis_results_tomotopy(lda, n_words)
    # Group patents by topic
    corpus = lda.infer(corpus)[0]
    for i, doc in enumerate(corpus):
        patents_per_topic[doc.get_topics(top_n=n_words)[0][0]].append(patent_ids[i])

    return results, patents_per_topic


def _topic_analysis_nmf(
    patents: QuerySet, patent_ids: List[int], n_topics: int, n_words: int, max_df: float
) -> Tuple[Dict, List[List[int]]]:
    """
    This function executes topic modeling for the given patents using NMF.

    Args:
        patents (QuerySet): The patents to execute the topic modeling for.
        patent_ids (List[int]): The ids of the patents, passed for performance reasons.
        n_topics (int): How many topics to generate.
        n_words (int): How many words per topic to display.
        max_df (float): The maximum document frequency for the tfidf vectorizer.
    Returns:
        Tuple[Dict, List[List[int]]]: The results of the topic analysis
        (words and weights per topic) and the patents per topic.
    """

    text_columns = patents.annotate(
        text=Concat(
            "title_processed",
            Value(" "),
            "abstract_processed",
            output_field=TextField(),
        )
    ).values_list("text", flat=True)

    tfidf_vectorizer = TfidfVectorizer(max_features=1000000, max_df=max_df)
    tfidf = tfidf_vectorizer.fit_transform(text_columns)
    nmf = NMF(n_components=n_topics, init="nndsvd", max_iter=10000).fit(tfidf)

    # Group patents by topic
    topics = tfidf_vectorizer.get_feature_names_out()
    patents_per_topic = [[] for _ in range(n_topics)]
    results = _format_topic_analysis_results_sklearn(nmf, topics, n_words)
    patent_topics = argmax(
        nmf.transform(tfidf_vectorizer.transform(text_columns)), axis=1
    )

    for i, topic in enumerate(patent_topics):
        patents_per_topic[topic].append(patent_ids[i])

    return results, patents_per_topic


def _format_topic_analysis_results_sklearn(
    model: NMF, feature_names: Iterable[str], n_words: int
) -> Dict:
    """
    This function formats the results of a topic analysis model when sklearn is used.

    Args:
        model (NMF): The sklearn model.
        feature_names (Iterable[str]): The feature names.
        n_words (int): The number of words per topic to be displayed.
    """

    # Check https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html

    topics = []
    for topic in model.components_:
        top_features_ind = topic.argsort()[: -n_words - 1 : -1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]
        topics.append({"words": top_features, "weights": weights.tolist()})
    return {"topics": topics, "coherence": "N/A"}


def _format_topic_analysis_results_tomotopy(model: Any, n_words: int) -> Dict:
    """
    This function formats the results of a topic analysis model when tomotopy is used.

    Args:
        model (Any): The tomotopy model.
        n_words (int): The number of words per topic to be displayed.
    """

    topics = []
    for k in range(model.k):
        topic_words = model.get_topic_words(k, top_n=n_words)
        topics.append(
            {
                "words": [word for word, _ in topic_words],
                "weights": [weight for _, weight in topic_words],
            }
        )
    return {
        "topics": topics,
        "coherence": f"{tp.coherence.Coherence(model, coherence='c_v', top_n=n_words).get_score():.3f}",
    }
