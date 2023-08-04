from datetime import timedelta, datetime
from random import randint
from typing import Type
from os import remove
from time import time
import json

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpRequest
from django.contrib.postgres.fields import ArrayField
from django.db.models.fields import TextField
from django.db.models.functions import Substr
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, OuterRef, Exists
from django.apps import apps
from django.db.models.aggregates import Count
from django.core.paginator import Paginator
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from tomotopy.utils import Corpus
import tomotopy as tp
from numpy import argmax

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
    paginator = Paginator(Patent.fetch_representation(patents), 50)

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

    # Check this StackOverflow thread to see how group by works in Django:
    # https://stackoverflow.com/a/629691/11718554

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    applications_per_year = (
        patents.values("application_year")
        .annotate(count=Count("id"))
        .order_by("application_year")
        .values("application_year", "count")
    )
    granted_patents_per_year = (
        patents.values("granted_year")
        .annotate(count=Count("id"))
        .order_by("granted_year")
        .values("granted_year", "count")
    )
    granted_patents_per_type_year = (
        patents.values("granted_year", "type")
        .annotate(count=Count("id"))
        .order_by("granted_year", "type")
        .values("granted_year", "type", "count")
    )
    granted_patents_per_office_year = (
        patents.values("granted_year", "office")
        .annotate(count=Count("id"))
        .order_by("granted_year", "office")
        .values("granted_year", "office", "count")
    )
    pct_protected_patents_per_year = (
        patents.filter(pct_data__granted=True)
        .values("granted_year")
        .annotate(count=Count("id"))
        .order_by("granted_year")
        .values("granted_year", "count")
    )
    granted_patents_per_cpc_year = (
        patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
        .values("granted_year", "cpc_section")
        .annotate(count=Count("id"))
        .order_by("granted_year", "cpc_section")
        .values("granted_year", "cpc_section", "count")
    )
    citations_made_per_year = (
        patents.values("citations__citation_year")
        .annotate(count=Count("id"))
        .order_by("citations__citation_year")
        .values("citations__citation_year", "count")
    )
    citations_received_per_year = (
        patents.values("cited_by__citation_year")
        .annotate(count=Count("id"))
        .order_by("cited_by__citation_year")
        .values("cited_by__citation_year", "count")
    )

    return JsonResponse(
        {
            "applications_per_year": {
                "": group_fields(applications_per_year, "application_year")
            },
            "granted_patents_per_year": {
                "": group_fields(granted_patents_per_year, "granted_year")
            },
            "granted_patents_per_type_year": group_fields(
                granted_patents_per_type_year, "type", "granted_year"
            ),
            "granted_patents_per_office_year": group_fields(
                granted_patents_per_office_year, "office", "granted_year"
            ),
            "pct_protected_patents_per_year": {
                "": group_fields(pct_protected_patents_per_year, "granted_year")
            },
            "granted_patents_per_cpc_year": group_fields(
                granted_patents_per_cpc_year, "cpc_section", "granted_year"
            ),
            "citations_made_per_year": {
                "": group_fields(citations_made_per_year, "citations__citation_year")
            },
            "citations_received_per_year": {
                "": group_fields(citations_received_per_year, "cited_by__citation_year")
            },
        }
    )


def entity_info(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    This view returns information about different entities matching the user's query.
    """

    if (patents := get_patents(request)) is None:
        return HttpResponseBadRequest("No patent query in the current session.")

    return JsonResponse(
        {
            "patent": {
                "pct": {
                    "Did not apply": patents.filter(pct_data__isnull=True).count(),
                    "Applied but not granted yet": patents.annotate(
                        all_not_granted=~Exists(
                            PCTData.objects.filter(
                                Q(granted=True), patent_id=OuterRef("pk")
                            )
                        )
                    )
                    .filter(all_not_granted=True, pct_data__isnull=False)
                    .count(),
                    "Granted": patents.filter(pct_data__granted=True).count(),
                },
                "type": group_fields(
                    patents.values("type").annotate(count=Count("id")).order_by(),
                    "type",
                ),
                "office": group_fields(
                    patents.values("office").annotate(count=Count("id")).order_by(),
                    "office",
                ),
            },
            "inventor": {
                "top_10": group_fields(
                    patents.annotate(
                        inventor=Concat(
                            "inventors__first_name", Value(" "), "inventors__last_name"
                        )
                    )
                    .filter(~Q(inventor__iregex=r"^\s*$"))
                    .values("inventor")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10],
                    "inventor",
                ),
                "locations": list(
                    patents.annotate(**get_coordinates("inventors__location__point"))
                    .filter(lat__isnull=False, lng__isnull=False)
                    .values("lat", "lng")
                    .annotate(count=Count("id"))
                    .order_by("-count")
                    .values("lat", "lng", "count")
                ),
            },
            "assignee": {
                "top_10": group_fields(
                    patents.annotate(
                        assignee=Concat(
                            "assignees__first_name",
                            Value(" "),
                            "assignees__last_name",
                            Value(" "),
                            "assignees__organization",
                        )
                    )
                    .filter(~Q(assignee__iregex=r"^\s*$"))
                    .values("assignee")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:10],
                    "assignee",
                ),
                "corporation_vs_individual": {
                    "Corporation": patents.filter(
                        assignees__is_organization=True
                    ).count(),
                    "Individual": patents.filter(
                        assignees__is_organization=False
                    ).count(),
                },
                "locations": list(
                    patents.annotate(**get_coordinates("assignees__location__point"))
                    .filter(lat__isnull=False, lng__isnull=False)
                    .values("lat", "lng")
                    .annotate(count=Count("id"))
                    .order_by("-count")
                    .values("lat", "lng", "count")
                ),
            },
            "cpc": {
                "section": group_fields(
                    patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
                    .values("cpc_section")
                    .annotate(count=Count("id"))
                    .order_by("-count"),
                    "cpc_section",
                ),
                "top_5_classes": group_fields(
                    patents.annotate(cpc_class=Substr("cpc_groups__cpc_group", 1, 3))
                    .values("cpc_class")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5],
                    "cpc_class",
                ),
                "top_5_subclasses": group_fields(
                    patents.annotate(cpc_subclass=Substr("cpc_groups__cpc_group", 1, 4))
                    .values("cpc_subclass")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5],
                    "cpc_subclass",
                ),
                "top_5_groups": group_fields(
                    patents.values("cpc_groups__cpc_group")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5],
                    "cpc_groups__cpc_group",
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

    model = request.GET.get("model", "MMF")
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

        tfidf_vectorizer = TfidfVectorizer(max_df=3, max_features=1000000)
        tfidf = tfidf_vectorizer.fit_transform(text_columns)
        nmf = NMF(n_components=n_topics, init="nndsvd").fit(tfidf)

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
        model.train()  # workers = 1 so that the results are reproducible

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

    local_network = PatentCitation.objects.filter(
        citing_patent_id__in=patent_ids, cited_patent_id__in=patent_ids
    )

    graph = local_network.annotate(
        citing_patent_code=Concat(
            "citing_patent__office", "citing_patent__office_patent_id"
        ),
        cited_patent_code=Concat(
            "cited_patent__office", "cited_patent__office_patent_id"
        ),
    ).values(
        "citing_patent_id",
        "citing_patent_code",
        "citing_patent__title",
        "citing_patent__granted_date",
        "cited_patent_id",
        "cited_patent_code",
        "cited_patent__title",
        "cited_patent__granted_date",
    )

    patent_annotation = {
        "patent": Concat(
            F("cited_patent__office"),
            F("cited_patent__office_patent_id"),
            Value(" - "),
            F("cited_patent__title"),
            output_field=TextField(),
        )
    }

    most_cited_patents_global = (
        PatentCitation.objects.filter(cited_patent_id__in=patent_ids)
        .annotate(**patent_annotation)
        .distinct("cited_patent__incoming_citations_count", "patent")
        .order_by("-cited_patent__incoming_citations_count", "patent")[:10]
        .values("patent", "cited_patent__incoming_citations_count")
    )

    most_cited_patents_local = (
        local_network.values("cited_patent")
        .annotate(**patent_annotation, count=Count("cited_patent_id"))
        .order_by("-count")[:10]
        .values("patent", "count")
    )

    return JsonResponse(
        {
            "graph": list(graph),
            "most_cited_patents_global": group_fields(
                most_cited_patents_global, "patent"
            ),
            "most_cited_patents_local": group_fields(
                most_cited_patents_local, "patent"
            ),
        },
        safe=False,
        encoder=DjangoJSONEncoder,
    )
