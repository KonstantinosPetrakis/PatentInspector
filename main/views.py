from django.shortcuts import render
from main.forms import *
from main.models import *
from django.contrib.postgres.search import SearchVector, SearchQuery
from time import time


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():
            t = time()
            patents = list(form.query_patents())
            patents_count = Patent.approximate_count()
            time_taken = time() - t
            return render(request, "main/result.html", 
                {"patents": patents, "time_taken": time_taken, "patents_count": patents_count})
    else:
        form = MainForm()
    return render(request, "main/index.html", {"form": form})
