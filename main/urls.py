from django.urls import path
import main.views as views

urlpatterns = [
    path("", views.index, name="index")
]
