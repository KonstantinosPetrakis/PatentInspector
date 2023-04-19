from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse_lazy as reverse
from django.db.models.functions import Length
from django.db.models import F
from main.models import *
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


def build_url(model, field=None):
    """
    Builds the url to fetch data for the given model class from the api.

    :param model: the class of the model to build the url for
    :param field: the field to filter the data by, defaults to None
    :return: the url to fetch data for the given model class from the api
    """

    if field is None: return reverse("model", args=[string_from_class(model)])
    return reverse("model-field", args=[string_from_class(model), field])


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
