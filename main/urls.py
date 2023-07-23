from django.urls import path
from django.urls import include, path

import main.views as views


urlpatterns = [
    path("", views.index, name="index"),
    path("api/", include("main.api_urls"))
]
