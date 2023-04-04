from django.urls import path

import main.views as views
from django.urls import include, path

urlpatterns = [
    path("", views.index, name="index"),
    path("api/", include("main.api_urls"))
]
