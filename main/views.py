from django.shortcuts import render
from main.forms import *
from main.models import *


def index(request):
    if request.method == "POST":
        form = MainForm(request=request)
        if form.is_valid():
            # Store the data in the session for later use (e.g export, pagination, ...)
            request.session["form_data"] = form.cleaned_data
    
            return render(request, "main/results.html")
    else:
        form = MainForm(request=request)
    return render(request, "main/index.html", {"form": form})
