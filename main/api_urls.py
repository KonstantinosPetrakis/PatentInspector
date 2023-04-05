from django.urls import path
import main.api as views


urlpatterns = [
    path("model/<model>/<query>", views.model, name="model"),
    path("model/<model>", views.model, name="model"),
    path("model-field/<model>/<field>/<query>", views.model_field, name="model-field"),
    path("model-field/<model>/<field>", views.model_field, name="model-field"),
]