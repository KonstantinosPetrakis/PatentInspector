from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.db.models.functions import Length, Substr, ExtractYear
from django.db.models.aggregates import Avg, StdDev, Count
from main.helpers import Median, WordCount, date_difference_in_years
from django.core.paginator import Paginator
from django.db.models import F, Q, OuterRef, Exists
from random import randint
from main.models import *
from os import remove
from time import time
import itertools
import json


CLASS_MAP = {
    "cpc_section": CPCSection,
    "cpc_class": CPCClass,
    "cpc_subclass": CPCSubclass,
    "cpc_group": CPCGroup,
    "inventor": Inventor,
    "assignee": Assignee,
}

REVERSE_CLASS_MAP = {v: k for k, v in CLASS_MAP.items()}


def class_from_string(string):
    """
    Returns the model class for the given string.

    :param string: the string to get the model class for
    :return: the model class for the given string
    """

    return CLASS_MAP[string] if string in CLASS_MAP else None


def string_from_class(_class):
    """
    Returns the string representation of the given model class.

    :param _class: the model class to get the string representation for
    :return: the string representation of the given model class
    """

    return REVERSE_CLASS_MAP[_class] if _class in REVERSE_CLASS_MAP else None


def id_and_title(model):
    """
    Returns the id and title fields for the given model. Title field is a form of representation of the model.

    :param model: the class of the model to get the id and title fields for
    :return: a tuple containing the id and title fields
    """

    map = {
        CPCSection: ("section", "title"),
        CPCClass: ("_class", "title"),
        CPCSubclass: ("subclass", "title"),
        CPCGroup: ("group", "title"),
    }
    return map[model] if model in map else None



def model(request, model, query=""):
    """
    This is a view for fetching model data for autocomplete form fields (ChoiceKeywordsField for now).
    If the content type of the request can be application/json or not.
    If it is application/json, it expects a json body containing a list of ids to fetch data for.
    If it is not application/json, it expects a query parameter to search for.
    
    :param request: the request object passed by django
    :param model: the model to fetch data for
    :param query: the query to search for, defaults to ""
    :return: a JsonResponse containing the model data or an HttpResponseBadRequest if the request is invalid
    """

    model = class_from_string(model)
    if model is None:
        return HttpResponseBadRequest("Invalid model name.")
    id, title = id_and_title(model)
    
    if request.META.get('CONTENT_TYPE', '') == "application/json":
        ids = json.loads(request.GET.get("ids", None))
        if ids is not None: 
            data = model.objects.filter(**{f"{id}__in": ids}).values(id, title)
            data = list(data.annotate(search_id=F(id), search_title=F(title)).values("search_id", "search_title"))
            return JsonResponse(data, safe=False)
        return HttpResponseBadRequest("Expected ids in json body.")
    
    data = model.objects.filter(**{f"{id}__iregex": f"^{query}"}).values(id, title)
    data = list(data.annotate(search_id=F(id), search_title=F(title)).values("search_id", "search_title"))
    return JsonResponse(data, safe=False)


def model_field(request, model, field, query=""):
    """
    This is a view for fetching model data for autocomplete form fields (ChoiceKeywordsField for now).
    
    It's the same as the model view, but instead of fetching 2 columns id and title 
    it fetches the column specified by the field parameter.
    
    For example, if the model is Location and the field is city, 
    it will fetch the distinct values of the city column of the Location model.

    :param request: the request object passed by django
    :param model: the model to fetch data for
    :param field: the field of the model to fetch data for
    :param query: the query to search data for, defaults to ""
    """

    model = class_from_string(model)
    if model is None:
        return HttpResponseBadRequest("Invalid model name.")
    
    if request.META.get('CONTENT_TYPE', '') == "application/json":
        distinct_field_values = json.loads(request.GET.get("ids", None))
        if distinct_field_values is not None:
            data = model.objects.filter(**{f"{field}__in": distinct_field_values}).distinct(field).values(field)
            # front-end expects search_id field, an identifier for the model
            # in our case, it's the same as the field value itself 
            # you can compare it with model function that goes like (search_id, title_field) 
            # instead of (field, field)
            data = list(data.annotate(search_id=F(field)).values("search_id")) 
            return JsonResponse(data, safe=False)
        return HttpResponseBadRequest("Expected ids in json body.")
    
    data = model.objects.filter(**{f"{field}__iregex": f"^{query}"}).values(field).distinct().order_by(Length(field))[:1000]
    data = list(data.annotate(search_id=F(field), search_title=F(field)).values("search_id"))
    return JsonResponse(data, safe=False)


def patents(request):
    """
    This view returns a list of patents, given a page number as a query parameter, it's used for pagination.
    """

    if (form_data := request.session.get("form_data", None)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")

    patents = Patent.fetch_representation(Patent.filter(form_data))

    page = int(request.GET.get("page", 1))
    paginator = Paginator(patents, 50)

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


def download_tsv(request):
    """
    This view allows the user to download the patents he filtered as a tsv file.
    """

    if (form_data := request.session.get("form_data", None)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")
    
    file_name = f"main/temp/{randint(0, 100) * time()}_patents.tsv"
    Patent.fetch_representation(Patent.filter(form_data)).to_csv(file_name, delimiter="\t")
    response = HttpResponse(content_type="text/tab-separated-values")
    response["Content-Disposition"] = f"attachment; filename={file_name}"
    response.write(open(file_name, "rb").read())
    remove(file_name)
    return response


def statistics(request):
    if (form_data := request.session.get("form_data", None)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")

    def calculate_statistics(field, function=None, display_name=None):
        if display_name is None: display_name = field

        return {
            f"avg_{display_name}": Avg(field),
            f"med_{display_name}": Median(field),
            f"std_dev_{display_name}": StdDev(field),
        }   if function is None else {
                f"avg_{display_name}": Avg(function(field)),
                f"med_{display_name}": Median(function(field)),
                f"std_dev_{display_name}": StdDev(function(field)),
            }

    def retrieve_statistics_from_result(bulk_result, fields):
        statistics.update({field: {
            "avg": bulk_result[f"avg_{field}"],
            "med": bulk_result[f"med_{field}"],
            "std_dev": bulk_result[f"std_dev_{field}"],
        } for field in fields})

    # coffee, 5.8k, 13.2s
    statistics = {}
    patents = Patent.filter(form_data)

    # Handle statistics that don't need joins
    retrieve_statistics_from_result(patents.annotate(
        years_to_get_granted=date_difference_in_years("granted_date", "application_filed_date")).aggregate(
            **calculate_statistics("years_to_get_granted"),
            **calculate_statistics("sheets_count"),
            **calculate_statistics("figures_count"),
            **calculate_statistics("claims_count"),
            **calculate_statistics("title", WordCount, "title_word_count"),
            **calculate_statistics("abstract", WordCount, "abstract_word_count"),
        ), ["years_to_get_granted", "sheets_count", "figures_count", "claims_count", "title_word_count", "abstract_word_count"])

    # Handle statistics that need joins one by one (one by one probably yields better performance)
    retrieve_statistics_from_result(patents.annotate(
        cpc_group_count=Count("cpc_groups", distinct=True)).aggregate(
            **calculate_statistics("cpc_group_count"),
        ), ["cpc_group_count"])

    retrieve_statistics_from_result(patents.annotate(
        inventor_count=Count("inventors", distinct=True)).aggregate(
            **calculate_statistics("inventor_count"),
        ), ["inventor_count"])

    retrieve_statistics_from_result(patents.annotate(
        assignee_count=Count("assignees", distinct=True)).aggregate(
           **calculate_statistics("assignee_count"),
        ), ["assignee_count"])

    retrieve_statistics_from_result(patents.annotate(
        incoming_citation_count=Count("citations", distinct=True)).aggregate(
            **calculate_statistics("incoming_citation_count"),
        ), ["incoming_citation_count"])
    
    retrieve_statistics_from_result(patents.annotate(
        outgoing_citation_count=Count("cited_by", distinct=True)).aggregate(
            **calculate_statistics("outgoing_citation_count"),
        ), ["outgoing_citation_count"])

    return JsonResponse({k.replace("_", " ").title(): v for k, v in statistics.items()})


def time_series(request):
    def format_output(records, grouped_by=None):
        if grouped_by is not None:
            # Create a dict with the distinct values of the grouped_by field as keys
            formatted_output = {distinct_val: {} for distinct_val in set(record[grouped_by] for record in records)}
            for record in records:
                formatted_output[record[grouped_by]].update({record["year"]: record["count"]})
            # Fill the missing years with 0
            distinct_years = list(set(record["year"] for record in records))
            for distinct_val in formatted_output:
                for year in distinct_years:
                    if year not in formatted_output[distinct_val]:
                        formatted_output[distinct_val][year] = 0
            formatted_output.pop(None, None) # remove empty values
            formatted_output = dict(sorted(formatted_output.items())) # sort by key
            return formatted_output
        else:
            return {record["year"]: record["count"] for record in records if record["year"]}
    
    if (form_data := request.session.get("form_data", None)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")

    patents = Patent.filter(form_data)

    applications_per_year = patents.annotate(year=ExtractYear("application_filed_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_year = patents.annotate(year=ExtractYear("granted_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_type_year = patents.annotate(year=ExtractYear("granted_date")).values("year", "type").annotate(count=Count("id")).order_by("year", "type").values("year", "type", "count")
    granted_patents_per_office_year = patents.annotate(year=ExtractYear("granted_date")).values("year", "office").annotate(count=Count("id")).order_by("year", "office").values("year", "office", "count")
    pct_protected_patents_per_year = patents.filter(pct_data__isnull=False).annotate(year=ExtractYear("granted_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    granted_patents_per_cpc_year = patents.annotate(year=ExtractYear("granted_date"), cpc_section=Substr("cpc_groups__cpc_group", 1, 1)).values("year", "cpc_section").annotate(count=Count("id")).order_by("year", "cpc_section").values("year", "cpc_section", "count")
    citations_made_per_year = patents.annotate(year=ExtractYear("citations__citation_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    citations_received_per_year = patents.annotate(year=ExtractYear("cited_by__citation_date")).values("year").annotate(count=Count("id")).order_by("year").values("year", "count")
    
    # Append the titles to the CPC sections codes
    cpc_section_titles = {record["section"]: record["title"] 
        for record in CPCSection.objects.all().values("section", "title")}
    granted_patents_per_cpc_year = {f"{k} - {cpc_section_titles[k]}": v 
        for k, v in format_output(granted_patents_per_cpc_year, "cpc_section").items()}

    return JsonResponse({
        "applications_per_year": format_output(applications_per_year),
        "granted_patents_per_year": format_output(granted_patents_per_year),
        "granted_patents_per_type_year": format_output(granted_patents_per_type_year, "type"),
        "granted_patents_per_office_year": format_output(granted_patents_per_office_year, "office"),
        "pct_protected_patents_per_year": format_output(pct_protected_patents_per_year),
        "granted_patents_per_cpc_year": granted_patents_per_cpc_year,
        "citations_made_per_year": format_output(citations_made_per_year),
        "citations_received_per_year": format_output(citations_received_per_year),
    })


def entity_info(request):
    def format_output(records, grouped_by=None):
        if grouped_by is not None:
            # Create a dict with the distinct values of the grouped_by field as keys
            formatted_output = {distinct_val: {} for distinct_val in set(record[grouped_by] for record in records)}
            for record in records:
                formatted_output[record[grouped_by]].update({record["year"]: record["count"]})
            # Fill the missing years with 0
            distinct_years = list(set(record["year"] for record in records))
            for distinct_val in formatted_output:
                for year in distinct_years:
                    if year not in formatted_output[distinct_val]:
                        formatted_output[distinct_val][year] = 0
            formatted_output.pop(None, None) # remove empty values
            formatted_output = dict(sorted(formatted_output.items())) # sort by key
            return formatted_output
        else:
            return {record["year"]: record["count"] for record in records if record["year"]}
    """
    https://github.com/Leaflet/Leaflet.heat

    * More graphs
        * Patent
            * Pie with PCT protection or not
            * Pie with patent type
            * Pie with patent office
        * Inventor
            * Pie with top 10 inventors
            * Pie with gender of inventors
            * Pie with organization, individual inventor count
            * A heatmap based on the location of the inventors
        * Assignee
            * A heatmap based on the location of the assignees
            * Pie with top 10 assignees
        * CPC
            * Pie with CPC sections
            * Pie with top 5 cpc classes
            * Pie with top 5 cpc subclasses
            * Pie with top 5 cpc groups
    """

    if (form_data := request.session.get("form_data", None)) is None: 
        return HttpResponseBadRequest("No patent query in the current session.")
    
    patents = Patent.filter(form_data)
    print(patents.values("type").annotate(count=Count("id")).order_by("count").values("type", "count"))
    return JsonResponse({
        "pct": {
            "not_pct": patents.filter(pct_data__isnull=True).count(),
            "pct_application": patents.annotate(all_not_granted=~Exists(PCTData.objects.filter(Q(granted=True), patent_id=OuterRef("pk")))).filter(all_not_granted=True, pct_data__isnull=False).count(),
            "pct_granted": patents.filter(pct_data__granted=True).count(),
        },
        "type": formatted_output(patents.values("type").annotate(count=Count("id")).order_by("count").values("type", "count"))),
    })


