from django.db.models import QuerySet
from django.core import serializers
from django.utils import timezone
from django.conf import settings
from django_q.tasks import Task
import pandas as pd

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

    if not settings.DEBUG and (count := patents.count()) > 40000:
        report.results = {
            "error": f"Too many patents ({count}) to process, please narrow down your search."
        }

        raise ValueError("Too many patents to process, please narrow down your search.")

    # Need to filter again because distinct + annotate is not supported by Django.
    patent_ids = list(patents.values_list("id", flat=True))
    patents = Patent.objects.filter(id__in=patent_ids)

    print("got patents")
    local_network_ids = list(PatentCitation.objects.filter(
        citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids
    ).values_list("id", flat=True))

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
        "topic_modeling": None,
        "citations": {
            "graph": PatentCitation.local_network_graph(local_network_ids),
            "most_cited_local": PatentCitation.most_cited_patents_local(
                local_network_ids
            ),
            "most_cited_global": PatentCitation.most_cited_patents_global(patent_ids),
        },
    }


def execute_topic_modeling(
    report: Report,
    method: str = "LDA",
    n_topics: int = 10,
    n_words: int = 10,
    start_date: str = None,
    end_date: str = None,
):
    """
    This function executes the topic modeling for the given report.

    Args:
        report (Report): The report to execute the topic modeling for.
        method (str, optional): The topic analysis method. Defaults to "LDA".
        n_topics (int, optional): The topics to be generated. Defaults to 10.
        n_words (int, optional): The words per topic to be displayed. Defaults to 10.
        start_date (str, optional): The start date used for CAGR classification. Defaults to None.
        end_date (str, optional):  The end date used for CAGR classification. Defaults to None.

    Returns:
        _type_: _description_
    """

    if (
        method == "LDA"
        and n_topics == 10
        and n_words == 10
        and start_date is None
        and end_date is None
    ):
        return  # No need to execute topic modeling if the parameters are the same as the default ones.


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

    report.datetime_analysis_ended = timezone.now()
    report.save()


def _create_excel(report: Report, patents: QuerySet = None):
    """
    This function creates the excel file for the report and stores it in the database.

    Args:
        report (Report): The report to create the excel file for.
        patents (QuerySet): The patents to include in the excel file if they are already fetched.
    """

    patents = patents if patents is not None else report.get_patents()

    df = pd.DataFrame(Patent.fetch_representation(patents).values())
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
