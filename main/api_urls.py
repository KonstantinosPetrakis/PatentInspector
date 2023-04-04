from django.urls import path
import main.api as views


urlpatterns = [
    path("cpc-sections/<query>", views.cpc_sections, name="cpc-sections"),
    path("cpc-sections", views.cpc_sections, name="cpc-sections"),
]