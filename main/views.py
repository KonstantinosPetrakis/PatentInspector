from django.core.paginator import Paginator
from django.shortcuts import render
from main.forms import *
from main.models import *
from time import time


def index(request):
    if request.method == "POST":
        form = MainForm(request=request)
        if form.is_valid():
            # Store the data in the session for later use (e.g export, pagination, ...)
            request.session["form_data"] = form.cleaned_data

            patents_total_count = Patent.approximate_count()
            patents = Patent.filter(form.cleaned_data)
    
            patents_count = len(patents) # All items are fetched here 

            return render(request, "main/results.html", {"patents_total_count": patents_total_count,
                "patents_count": patents_count})
    else:
        form = MainForm(request=request)
    return render(request, "main/index.html", {"form": form})
