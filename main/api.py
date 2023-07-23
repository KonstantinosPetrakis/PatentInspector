from datetime import timedelta, datetime
from random import randint
from typing import Type
from os import remove
from time import time
import json

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpRequest
from django.db.models.functions import Substr, ExtractYear
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, OuterRef, Exists
from django.apps import apps
from django.db.models.aggregates import Count
from django.core.paginator import Paginator
from django.conf import settings
from sklearn.decomposition import NMF
import tomotopy as tp


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

    try: return apps.get_model("main", string)
    except LookupError: return None


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


def records_field_from_exact_list(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
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

    model, wanted_fields, exact_field, exact_values = [request.GET.get(k, None)
        for k in ("model", "wanted-fields", "exact-field", "exact-values")]

    if any([f is None for f in (model, wanted_fields, exact_field, exact_values)]):
        return HttpResponseBadRequest("Missing query parameters.")

    model = class_from_string(model)
    exact_values = exact_values.split("~#") # ~# is the separator between values instead of commas
    wanted_fields = wanted_fields.split(",")

    if len(wanted_fields) == 1:
        data = model.objects.filter(**{f"{exact_field}__in": exact_values}).values_list(
            *wanted_fields, flat=True)
    else:
        data = model.objects.filter(**{f"{exact_field}__in": exact_values}).values(*wanted_fields)
    
    return JsonResponse(list(data), safe=False)

    
def records_field_from_query(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
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

    model, wanted_fields, query_field, query = [request.GET.get(k, None) 
        for k in ("model", "wanted-fields", "query-field", "query")]
    
    if any([f is None for f in (model, wanted_fields, query_field, query)]):
        return HttpResponseBadRequest("Missing query parameters.")
    
    min_query_length = get_min_query_length(class_from_string(model), query_field)
    if len(query) < min_query_length: return JsonResponse([], safe=False)

    model = class_from_string(model)
    wanted_fields = wanted_fields.split(",")

    if len(wanted_fields) == 1:
        data = model.objects.filter(**{f"{query_field}__istartswith": query}).values_list(
            wanted_fields[0], flat=True).distinct().order_by(wanted_fields[0])[: 500]
    else:
        data = model.objects.filter(**{f"{query_field}__istartswith": query}).values(
            *wanted_fields).distinct().order_by(wanted_fields[0])[: 500]

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
    paginator = Paginator(Patent.fetch_representation(patents), 50)

    return JsonResponse({
        "patents": list(paginator.page(page).object_list.values()),
        "page": page,
        "selected_record_count": paginator.count,
        "total_record_count": Patent.approximate_count(),
        "page_range": list(paginator.get_elided_page_range(page)),
        "inventor_circle": (f"{inventor_circle['lat']},{inventor_circle['lng']},{inventor_circle['radius']}"
            if (inventor_circle := form_data.get("inventor_location", None)) is not None else ""),
        "assignee_circle": (f"{assignee_circle['lat']},{assignee_circle['lng']},{assignee_circle['radius']}"
            if (assignee_circle := form_data.get("assignee_location", None)) is not None else ""),
    })


def download_tsv(request: HttpRequest) -> HttpResponse | HttpResponseBadRequest:
    """
    This view allows the user to download the patents he filtered as a tsv file.

    Args:
        request (HttpRequest): The request object passed by django.
    
    Returns:
        HttpResponse: The tsv file or an error response.
    """

    if (patents := get_patents(request)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")
    
    file_name = f"main/temp/{randint(0, 100) * time()}_patents.tsv"
    Patent.fetch_representation(patents).to_csv(file_name, delimiter="\t")
    response = HttpResponse(content_type="text/tab-separated-values")
    response["Content-Disposition"] = f"attachment; filename={file_name}"
    response.write(open(file_name, "rb").read())
    remove(file_name)
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

    # Handle statistics that don't need joins
    statistics.update(format_statistics(patents.annotate(
        years_to_get_granted=date_difference_in_years("granted_date", "application_filed_date")).aggregate(
            **calculate_statistics("years_to_get_granted"),
            **calculate_statistics("sheets_count"),
            **calculate_statistics("figures_count"),
            **calculate_statistics("claims_count"),
            **calculate_statistics("title", WordCount, "title_word_count"),
            **calculate_statistics("abstract", WordCount, "abstract_word_count"))))

    # Handle statistics that need joins one by one (single query for each one probably yields better performance)
    statistics.update(format_statistics(patents.annotate(
        cpc_group_count=Count("cpc_groups")).aggregate(**calculate_statistics("cpc_group_count"))))

    statistics.update(format_statistics(patents.annotate(
        inventor_count=Count("inventors")).aggregate(**calculate_statistics("inventor_count"))))

    statistics.update(format_statistics(patents.annotate(
        assignee_count=Count("assignees")).aggregate(**calculate_statistics("assignee_count"))))

    statistics.update(format_statistics(patents.annotate(incoming_citation_count=Count("citations")).aggregate(
        **calculate_statistics("incoming_citation_count"))))
    
    statistics.update(format_statistics(patents.annotate(
        outgoing_citation_count=Count("cited_by")).aggregate(**calculate_statistics("outgoing_citation_count"))))
    
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

    applications_per_year = patents.annotate(year=ExtractYear("application_filed_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_year = patents.annotate(year=ExtractYear("granted_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_type_year = patents.annotate(year=ExtractYear("granted_date")).values("year", "type").annotate(count=Count("id")).order_by("year", "type").values("year", "type", "count")
    granted_patents_per_office_year = patents.annotate(year=ExtractYear("granted_date")).values("year", "office").annotate(count=Count("id")).order_by("year", "office").values("year", "office", "count")
    pct_protected_patents_per_year = patents.filter(pct_data__isnull=False).annotate(year=ExtractYear("granted_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_cpc_year = patents.annotate(year=ExtractYear("granted_date"), cpc_section=Substr("cpc_groups__cpc_group", 1, 1)).values("year", "cpc_section").annotate(count=Count("id")).order_by("year", "cpc_section").values("year", "cpc_section", "count")
    citations_made_per_year = patents.annotate(year=ExtractYear("citations__citation_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    citations_received_per_year = patents.annotate(year=ExtractYear("cited_by__citation_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    
    return JsonResponse({
        "applications_per_year": group_fields(applications_per_year),
        "granted_patents_per_year": group_fields(granted_patents_per_year),
        "granted_patents_per_type_year": group_fields(granted_patents_per_type_year, "type"),
        "granted_patents_per_office_year": group_fields(granted_patents_per_office_year, "office"),
        "pct_protected_patents_per_year": group_fields(pct_protected_patents_per_year),
        "granted_patents_per_cpc_year": append_title_to_cpc(group_fields(granted_patents_per_cpc_year, "cpc_section")),
        "citations_made_per_year": group_fields(citations_made_per_year),
        "citations_received_per_year": group_fields(citations_received_per_year),
    })


def entity_info(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns information about different entities matching the user's query.
    """

    if (patents := get_patents(request)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")

    return JsonResponse({
        "patent": {
            "pct": {
                "Did not apply": patents.filter(pct_data__isnull=True).count(),
                "Applied but not granted yet": patents.annotate(all_not_granted=~Exists(PCTData.objects.filter(Q(granted=True), patent_id=OuterRef("pk")))).filter(all_not_granted=True, pct_data__isnull=False).count(),
                "Granted": patents.filter(pct_data__granted=True).count(),
            },
            "type": group_fields(patents.values("type").annotate(count=Count("id")).order_by(), "type"),
            "office": group_fields(patents.values("office").annotate(count=Count("id")).order_by(), "office"),
        },
        "inventor": {
            "top_10": group_fields(patents.annotate(inventor=Concat("inventors__first_name", Value(" "), "inventors__last_name")).filter(~Q(inventor=" ")).values("inventor").annotate(count=Count("id")).order_by("-count")[:10], "inventor"),
            "locations": list(patents.annotate(**get_coordinates("inventors__location__point")).filter(lat__isnull=False, lng__isnull=False).values("lat", "lng").annotate(count=Count("id")).order_by("-count").values("lat", "lng", "count"))
        },
        "assignee": {
            "top_10": group_fields(patents.annotate(assignee=Concat("assignees__first_name", Value(" "), "assignees__last_name", Value(" "), "assignees__organization")).filter(~Q(assignee="  ")).values("assignee").annotate(count=Count("id")).order_by("-count")[:10], "assignee"),
            "corporation_vs_individual": {
                "Corporation": patents.filter(Q(assignees__isnull=False) & string_is_empty("assignees__first_name") & string_is_empty("assignees__last_name")).count(),
                "Individual": patents.filter(Q(assignees__isnull=False) & string_is_empty("assignees__organization")).count(),
            },
            "locations": list(patents.annotate(**get_coordinates("assignees__location__point")).filter(lat__isnull=False, lng__isnull=False).values("lat", "lng").annotate(count=Count("id")).order_by("-count").values("lat", "lng", "count"))
        },
        "cpc": {
            "section": append_title_to_cpc(group_fields(patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1)).values("cpc_section").annotate(count=Count("id")).order_by("-count"), "cpc_section")),
            "top_5_classes": append_title_to_cpc(group_fields(patents.annotate(cpc_class=Substr("cpc_groups__cpc_group", 1, 3)).values("cpc_class").annotate(count=Count("id")).order_by("-count")[:5], "cpc_class")),
            "top_5_subclasses": append_title_to_cpc(group_fields(patents.annotate(cpc_subclass=Substr("cpc_groups__cpc_group", 1, 4)).values("cpc_subclass").annotate(count=Count("id")).order_by("-count")[:5], "cpc_subclass")),
            "top_5_groups": append_title_to_cpc(group_fields(patents.values("cpc_groups__cpc_group").annotate(count=Count("id")).order_by("-count")[:5], "cpc_groups__cpc_group")),
        }
    })


def topic_modeling(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns the results of the topic modeling analysis.

    Args:
        request (HttpRequest): The request object passed by django.
    
    Returns:
        JsonResponse | HttpResponseBadRequest: An object containing the topic modeling
        results or an error response.
    """

    if (patents := get_patents(request)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")
    
    tp_remove_top = 10
    n_topics = 10
    n_top_words = 10
    tp_model_map = {
        "LDA": tp.LDAModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "LLDA": tp.LLDAModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "SLDA": tp.SLDAModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "DMR": tp.DMRModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "HDP": tp.HDPModel(rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "HLDA": tp.HLDAModel(rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "MGLDA": tp.MGLDAModel(rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "PA": tp.PAModel(rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "HPA": tp.HPAModel(rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "CTM": tp.CTModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
        "PTM": tp.PTModel(k=n_topics, rm_top=tp_remove_top, seed=settings.RANDOM_SEED),
    }

    patents_count = patents.count()
    
    model = request.GET.get("model", "LDA")
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
        tfidf_vectorizer, tfidf = patents_to_tfidf(patents)
        nmf = NMF(n_components=n_topics, init='nndsvd', random_state=settings.RANDOM_STATE).fit(tfidf)

        # Group patents by topic
        topics = tfidf_vectorizer.get_feature_names_out()
        patents_per_topic = [[] for _ in range(n_topics)]
        results = format_topic_analysis_results_sklearn(nmf, topics, n_top_words)
        for patent in patents:
            patents_per_topic[predict_patent_topic(nmf, patent, tfidf_vectorizer)].append(patent.id)

    elif model in tp_model_map:
        text_columns = patents.annotate(content=Concat('title', Value(' '), 'abstract', output_field=fields.TextField())).values_list('content', flat=True)
        model = tp_model_map[model]
        for doc in prepare_texts_for_tomotopy_analysis(text_columns): model.add_doc(doc)
        model.train(500)
        patents_per_topic = [[] for _ in range(model.k)]
        results = format_topic_analysis_results_tomotopy(model, n_top_words)
        # Group patents by topic
        for patent in patents:
            patents_per_topic[predict_patent_topic(model, patent)].append(patent.id)
    else:
        return HttpResponseBadRequest("Invalid model name.")

    # Calculate the ratio and cagr of patents per topic
    for i, patents in enumerate(patents_per_topic):
        patents_in_end_year = Patent.objects.filter(id__in=patents, granted_date__gte=end_date - timedelta(days=365), granted_date__lte=end_date).count()
        patents_in_start_year = Patent.objects.filter(id__in=patents, granted_date__gte=start_date - timedelta(days=365), granted_date__lte=start_date).count()
        results["topics"][i]["ratio"] = len(patents) / patents_count
        # The +1 is to avoid division by zero
        results["topics"][i]["cagr"] = (patents_in_end_year / (patents_in_start_year + 1)) ** (1 / years_diff) - 1
    # Echo the start and end dates in case they were not specified
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
    
    graph = PatentCitation.objects.filter(citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids).annotate(
        citing_patent_code=Concat("citing_patent__office", "citing_patent__office_patent_id"),
        cited_patent_code=Concat("cited_patent__office", "cited_patent__office_patent_id")
    ).values(
        "citing_patent_id", "citing_patent_code", "citing_patent__title", "citing_patent__granted_date",
        "cited_patent_id", "cited_patent_code", "cited_patent__title", "cited_patent__granted_date")

    cited_patent_repr = {"patent": Concat("cited_patent__office", "cited_patent__office_patent_id", Value(" - "), Cast("cited_patent__title", fields.CharField()))}
    most_cited_patents_global = PatentCitation.objects.filter(cited_patent_id__in=patent_ids).annotate(**cited_patent_repr).values("patent").annotate(count=Count("id")).order_by("-count")[:10]
    most_cited_patents_local = PatentCitation.objects.filter(citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids).annotate(**cited_patent_repr).values("patent").annotate(count=Count("id")).order_by("-count")[:10]

    return JsonResponse({
        "graph": list(graph),
        "most_cited_patents_global": group_fields(most_cited_patents_global, "patent"),
        "most_cited_patents_local":  group_fields(most_cited_patents_local, "patent"),
    }, safe=False, encoder=DjangoJSONEncoder)
