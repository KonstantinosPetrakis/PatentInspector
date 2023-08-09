from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime
from random import randint
from typing import Type
from os import remove
from time import time
import json

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpRequest
from django.contrib.postgres.fields import ArrayField
from django.db.models.fields import TextField
from django.core.serializers.json import DjangoJSONEncoder
from django.apps import apps
from django.db.models.aggregates import Count
from django.core.paginator import Paginator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from tomotopy.utils import Corpus
import tomotopy as tp
from numpy import argmax
import pandas as pd

from main.helpers import *
from main.models import *


# ---------------- Constants and helpers ----------------

MIN_QUERY_LENGTH = {
    (CPCSubclass, "subclass"): 1,
    (CPCGroup, "group"): 3,
    (Inventor, "first_name"): 2,
    (Inventor, "last_name"): 2,
    (Assignee, "first_name"): 2,
    (Assignee, "last_name"): 2,
    (Assignee, "organization"): 2,
}


def class_from_string(string: str) -> Type | None:
    """
    This function returns the model class from the given string.

    Args:
        string (str): The string representation of the model class.

    Returns:
        Type: The model class or None if the string is not a valid model class.
    """

    try:
        return apps.get_model("main", string)
    except LookupError:
        return None


def string_from_class(_class: Type) -> str:
    """
    This function returns the string representation of the given model class.

    Args:
        _class (Type): The model class.

    Returns:
        str: The string representation of the model class.
    """

    return _class.__name__


def get_min_query_length(model: Type, field: str = None) -> int:
    """
    This function returns the minimum query length for the given model and field.

    Args:
        model (Type): The model class.
        field (str, optional): The field of the model. Defaults to None.

    Returns:
        int: The minimum query length.
    """

    return MIN_QUERY_LENGTH[(model, field)] if (model, field) in MIN_QUERY_LENGTH else 0


def get_form_data(request: HttpRequest) -> dict | None:
    """
    This function returns the form data from the session.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        dict | None: The form data or None if it's not in the session.
    """

    if (form_data_str := request.session.get("form_data", None)) is not None:
        return json.loads(form_data_str)


def get_patent_ids(request: HttpRequest) -> list[int] | None:
    """
    This function returns the patent ids from the session.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        list[int] | None: The patent ids or None if they're not in the session.
    """

    if (patent_ids_str := request.session.get("patent_ids", None)) is not None:
        return json.loads(patent_ids_str)


def get_patents(request: HttpRequest) -> models.QuerySet[Patent] | None:
    """
    This function returns the patents based on the ids stored in the session.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        models.QuerySet[Patent] | None: The patents or None if they're not in the session.
    """

    if (patent_ids := get_patent_ids(request)) is not None:
        return Patent.objects.filter(id__in=patent_ids)


# ---------------- Route handlers ----------------


def records_field_from_exact_list(
    request: HttpRequest,
) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns a list of records, given a list of exact values for a field.

    Args:
        request (HttpRequest): The request object passed by django, the request method must contain
        the following query parameters:
        * model: The model class.
        * wanted-fields: The wanted field of the model.
        * exact-field: The field of the model to filter by exact values.
        * exact-values: The exact values to filter by.

    Returns:
        JsonResponse | HttpResponseBadRequest: A list containing the wanted_field from the filtered
        records or an error response.
    """

    model, wanted_fields, exact_field, exact_values = [
        request.GET.get(k, None)
        for k in ("model", "wanted-fields", "exact-field", "exact-values")
    ]

    if any([f is None for f in (model, wanted_fields, exact_field, exact_values)]):
        return HttpResponseBadRequest("Missing query parameters.")

    model = class_from_string(model)
    exact_values = exact_values.split(
        "~#"
    )  # ~# is the separator between values instead of commas
    wanted_fields = wanted_fields.split(",")

    if len(wanted_fields) == 1:
        data = model.objects.filter(**{f"{exact_field}__in": exact_values}).values_list(
            *wanted_fields, flat=True
        )
    else:
        data = model.objects.filter(**{f"{exact_field}__in": exact_values}).values(
            *wanted_fields
        )

    return JsonResponse(list(data), safe=False)


def records_field_from_query(
    request: HttpRequest,
) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns a list of records, given a query string.

    Args:
        request (HttpRequest): The request object passed by django, the request method must contain
        the following query parameters:
        * model: The model class.
        * wanted-fields: The wanted fields of the model.
        * query-field: The field of the model to filter by.
        * query: The query string to filter by.

    Returns:
        JsonResponse | HttpResponseBadRequest: An array containing the wanted_fields
        from the filtered records or an error response.
    """

    model, wanted_fields, query_field, query = [
        request.GET.get(k, None)
        for k in ("model", "wanted-fields", "query-field", "query")
    ]

    if None in [model, wanted_fields, query_field, query]:
        return HttpResponseBadRequest("Missing query parameters.")

    min_query_length = get_min_query_length(class_from_string(model), query_field)
    if len(query) < min_query_length:
        return JsonResponse([], safe=False)

    model = class_from_string(model)
    wanted_fields = wanted_fields.split(",")

    if len(wanted_fields) == 1:
        data = (
            model.objects.filter(**{f"{query_field}__istartswith": query})
            .values_list(wanted_fields[0], flat=True)
            .distinct()
            .order_by(wanted_fields[0])[:500]
        )
    else:
        data = (
            model.objects.filter(**{f"{query_field}__istartswith": query})
            .values(*wanted_fields)
            .distinct()
            .order_by(wanted_fields[0])[:500]
        )

    return JsonResponse(list(data), safe=False)


def patents(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns a list of patents, given a page number as a query parameter, it's used for pagination.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the patents and other info or
        an error response.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    form_data = get_form_data(request)
    page = int(request.GET.get("page", 1))
    paginator = Paginator(Patent.fetch_minimal_representation(patents), 25)

    return JsonResponse(
        {
            "patents": list(paginator.page(page).object_list.values()),
            "page": page,
            "selected_record_count": paginator.count,
            "total_record_count": Patent.approximate_count(),
            "page_range": list(paginator.get_elided_page_range(page)),
            "inventor_circle": (
                f"{inventor_circle['lat']},{inventor_circle['lng']},{inventor_circle['radius']}"
                if (inventor_circle := form_data.get("inventor_location", None))
                is not None
                else ""
            ),
            "assignee_circle": (
                f"{assignee_circle['lat']},{assignee_circle['lng']},{assignee_circle['radius']}"
                if (assignee_circle := form_data.get("assignee_location", None))
                is not None
                else ""
            ),
        }
    )


def download_excel(request: HttpRequest) -> HttpResponse | HttpResponseBadRequest:
    """
    This view allows the user to download the patents he filtered as an excel file.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        HttpResponse: The excel file or an error response.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    base_file_name = f"main/temp/{randint(0, 100) * time()}_patents"
    tsv_file_name = f"{base_file_name}.tsv"
    excel_file_name = f"{base_file_name}.xlsx"

    Patent.fetch_representation(patents).to_csv(tsv_file_name, delimiter="\t")
    pd.read_csv(tsv_file_name, delimiter="\t").to_excel(excel_file_name, index=False)

    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f"attachment; filename={excel_file_name}"
    response.write(open(excel_file_name, "rb").read())

    remove(tsv_file_name)
    remove(excel_file_name)
    return response


def statistics(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns statistics about the patents that match the user's query.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the statistics or an error response.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

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
        statistics.update(calculate_statistics(field))

    statistics = format_statistics(patents.aggregate(**statistics))

    return JsonResponse({k.replace("_", " ").title(): v for k, v in statistics.items()})


def time_series(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns a set of time series based on the user's query.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the time series or an error response.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    patent_ids = get_patent_ids(request)

    def thread_worker(i):
        method_name = [
            "applications_per_year",
            "granted_patents_per_year",
            "granted_patents_per_type_year",
            "granted_patents_per_office_year",
            "pct_protected_patents_per_year",
            "granted_patents_per_cpc_year",
            "citations_made_per_year",
            "citations_received_per_year",
        ][i]

        method = getattr(Patent, method_name)
        return method(patents) if i < 6 else method(patent_ids)

    with ThreadPoolExecutor(max_workers=8) as executor:
        (
            applications_per_year,
            granted_patents_per_year,
            granted_patents_per_type_year,
            granted_patents_per_office_year,
            pct_protected_patents_per_year,
            granted_patents_per_cpc_year,
            citations_made_per_year,
            citations_received_per_year,
        ) = executor.map(thread_worker, range(8))

    return JsonResponse(
        {
            "applications_per_year": {
                "": group_fields(applications_per_year, ["application_year"])
            },
            "granted_patents_per_year": {
                "": group_fields(granted_patents_per_year, ["granted_year"])
            },
            "granted_patents_per_type_year": group_fields(
                granted_patents_per_type_year, ["type", "granted_year"]
            ),
            "granted_patents_per_office_year": group_fields(
                granted_patents_per_office_year, ["office", "granted_year"]
            ),
            "pct_protected_patents_per_year": {
                "": group_fields(pct_protected_patents_per_year, ["granted_year"])
            },
            "granted_patents_per_cpc_year": group_fields(
                granted_patents_per_cpc_year, ["cpc_section", "granted_year"]
            ),
            "citations_made_per_year": {
                "": group_fields(citations_made_per_year, ["citation_year"])
            },
            "citations_received_per_year": {
                "": group_fields(citations_received_per_year, ["citation_year"])
            },
        }
    )


def entity_info(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns information about different entities matching the user's query.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    def thread_worker(i):
        method_name = [
            "pct_not_applied",
            "pct_not_granted",
            "pct_granted",
            "types",
            "offices",
            "top_10_inventors",
            "inventor_locations",
            "top_10_assignees",
            "corporation_assignees_count",
            "individual_assignees_count",
            "assignee_locations",
            "cpc_sections",
            "top_5_cpc_classes",
            "top_5_cpc_subclasses",
            "top_5_cpc_groups",
        ][i]

        method = getattr(Patent, method_name)
        return method(patents)

    with ThreadPoolExecutor(max_workers=15) as executor:
        (
            pct_not_applied,
            pct_not_granted,
            pct_granted,
            types,
            offices,
            top_10_inventors,
            inventor_locations,
            top_10_assignees,
            corporation_assignees_count,
            individual_assignees_count,
            assignee_locations,
            cpc_sections,
            top_5_cpc_classes,
            top_5_cpc_subclasses,
            top_5_cpc_groups,
        ) = executor.map(thread_worker, range(15))

    return JsonResponse(
        {
            "patent": {
                "pct": {
                    "Did not apply": pct_not_applied,
                    "Applied but not granted yet": pct_not_granted,
                    "Granted": pct_granted,
                },
                "type": group_fields(types, ["type"]),
                "office": group_fields(offices, ["office"]),
            },
            "inventor": {
                "top_10": group_fields(top_10_inventors, ["inventor"]),
                "locations": inventor_locations,
            },
            "assignee": {
                "top_10": group_fields(top_10_assignees, ["assignee"]),
                "corporation_vs_individual": {
                    "Corporation": corporation_assignees_count,
                    "Individual": individual_assignees_count,
                },
                "locations": assignee_locations,
            },
            "cpc": {
                "section": group_fields(
                    cpc_sections,
                    ["cpc_section"],
                ),
                "top_5_classes": group_fields(
                    top_5_cpc_classes,
                    ["cpc_class"],
                ),
                "top_5_subclasses": group_fields(
                    top_5_cpc_subclasses,
                    ["cpc_subclass"],
                ),
                "top_5_groups": group_fields(
                    top_5_cpc_groups,
                    ["cpc_groups__cpc_group"],
                ),
            },
        }
    )


def topic_modeling(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns the results of the topic modeling analysis.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the topic modeling
        results or an error response.
    """

    n_topics = 10
    n_top_words = 10
    tp_args = {"k": n_topics}
    tp_model_map = {
        "LDA": tp.LDAModel(**tp_args),
        "LLDA": tp.LLDAModel(**tp_args),
        "SLDA": tp.SLDAModel(**tp_args),
        "DMR": tp.DMRModel(**tp_args),
        "CTM": tp.CTModel(**tp_args),
        "PTM": tp.PTModel(**tp_args),
    }

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    model = request.GET.get("model", "LDA")
    if model not in list(tp_model_map.keys()) + ["NMF"]:
        return HttpResponseBadRequest("Invalid model.")

    patent_ids = get_patent_ids(request)
    patents_count = len(patent_ids)

    if (end_date := request.GET.get("end_date", None)) is None:
        end_date = patents.aggregate(max_date=Max("granted_date"))["max_date"]
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    if (start_date := request.GET.get("start_date", None)) is None:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    years_diff = (end_date - start_date).days / 365

    if model == "NMF":
        patents = patents.annotate(
            text=Concat(
                "title_processed",
                Value(" "),
                "abstract_processed",
                output_field=TextField(),
            )
        )
        text_columns = patents.values_list("text", flat=True)

        tfidf_vectorizer = TfidfVectorizer(max_features=1000000)
        tfidf = tfidf_vectorizer.fit_transform(text_columns)
        nmf = NMF(n_components=n_topics, init="nndsvd", max_iter=2000).fit(tfidf)

        # Group patents by topic
        topics = tfidf_vectorizer.get_feature_names_out()
        patents_per_topic = [[] for _ in range(n_topics)]
        results = format_topic_analysis_results_sklearn(nmf, topics, n_top_words)
        patent_topics = argmax(
            nmf.transform(tfidf_vectorizer.transform(text_columns)), axis=1
        )

        for i, topic in enumerate(patent_topics):
            patents_per_topic[topic].append(patent_ids[i])

    else:
        patents = patents.annotate(
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
        )

        model = tp_model_map[model]
        corpus = Corpus()
        for patent in patents:
            corpus.add_doc(patent.doc)

        model.add_corpus(corpus)
        model.train(iter=500)

        patents_per_topic = [[] for _ in range(model.k)]
        results = format_topic_analysis_results_tomotopy(model, n_top_words)
        # Group patents by topic
        corpus = model.infer(corpus)[0]
        for i, doc in enumerate(corpus):
            patents_per_topic[doc.get_topics(top_n=n_top_words)[0][0]].append(
                patent_ids[i]
            )

    # Calculate the ratio and cagr of patents per topic
    for i, patents in enumerate(patents_per_topic):
        patents_in_end_year = Patent.objects.filter(
            id__in=patents,
            granted_date__gte=end_date - timedelta(days=365),
            granted_date__lte=end_date,
        ).count()
        patents_in_start_year = Patent.objects.filter(
            id__in=patents,
            granted_date__gte=start_date - timedelta(days=365),
            granted_date__lte=start_date,
        ).count()
        results["topics"][i]["ratio"] = len(patents) / patents_count
        # The +1 is to avoid division by zero
        results["topics"][i]["cagr"] = (
            patents_in_end_year / (patents_in_start_year + 1)
        ) ** (1 / years_diff) - 1

    # Echo (return as well) the start and end dates in case they were not specified
    results["start_date"] = start_date.strftime("%Y-%m-%d")
    results["end_date"] = end_date.strftime("%Y-%m-%d")
    return JsonResponse(results, safe=False)


def citation_data(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns the local patent to patent (P2P) citation graph and some data about the most
    cited patents for the patents matching the user's query.

    Args:
        request (HttpRequest): The request object passed by django.

    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the citation graph and the most
        cited patents or an error response.
    """

    if (patent_ids := get_patent_ids(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    def thread_worker(i):
        if i == 0:
            return PatentCitation.local_network_graph(local_network_ids)
        elif i == 1:
            return PatentCitation.most_cited_patents_local(local_network_ids)
        else:
            return PatentCitation.most_cited_patents_global(patent_ids)

    local_network_ids = list(
        PatentCitation.objects.filter(
            citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids
        ).values_list("id", flat=True)
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        graph, most_cited_patents_local, most_cited_patents_global = executor.map(
            thread_worker, range(3)
        )

    return JsonResponse(
        {
            "graph": graph,
            "most_cited_patents_global": group_fields(
                most_cited_patents_global, ["patent"]
            ),
            "most_cited_patents_local": group_fields(
                most_cited_patents_local, ["patent"]
            ),
        }
    )
