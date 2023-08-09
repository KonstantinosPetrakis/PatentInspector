from django.urls import path

import main.api as views


urlpatterns = [
    path("records-field-from-exact-list", views.records_field_from_exact_list, 
        name="records-field-from-exact-list"),
    path("records-field-from-query", views.records_field_from_query, 
        name="records-field-from-query"),
    path("patents", views.patents, name="patents"),
    path("download-excel", views.download_excel, name="download-excel"),
    path("statistics", views.statistics, name="statistics"),
    path("time-series", views.time_series, name="time-series"),
    path("entity-info", views.entity_info, name="entity-info"),
    path("topic-modeling", views.topic_modeling, name="topic-modeling"),
    path("citation-data", views.citation_data, name="citation-data"),
]
