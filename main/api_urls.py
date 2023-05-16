from django.urls import reverse_lazy as reverse
from django.urls import path
import main.api as views


urlpatterns = [
    path("model/<model>/<query>", views.model, name="model"),
    path("model/<model>", views.model, name="model"),
    path("model-field/<model>/<field>/<query>", views.model_field, name="model-field"),
    path("model-field/<model>/<field>", views.model_field, name="model-field"),
    path("patents", views.patents, name="patents"),
    path("download-tsv", views.download_tsv, name="download-tsv"),
    path("statistics", views.statistics, name="statistics"),
    path("time-series", views.time_series, name="time-series"),
    path("entity-info", views.entity_info, name="entity-info"),
    path("topic-modeling", views.topic_modeling, name="topic-modeling"),
    path("citation-graph", views.citation_graph, name="citation-graph"),
]


def build_url(model, field=None):
    """
    Builds the url to fetch data for the given model class from the api.

    :param model: the class of the model to build the url for
    :param field: the field to filter the data by, defaults to None
    :return: the url to fetch data for the given model class from the api
    """

    if field is None: return reverse("model", args=[views.string_from_class(model)])
    return reverse("model-field", args=[views.string_from_class(model), field])