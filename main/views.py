from django.shortcuts import render
from main.forms import *
from main.models import *
from time import time


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():            
            t = time()
            patents = list(form.query_patents())
            patents_count = Patent.approximate_count()

            inventor_circle = ",".join([str(val) for val in form.cleaned_data["inventor_location"].values()]) if form.cleaned_data["inventor_location"] else ""
            assignee_circle = ",".join(str(val) for val in form.cleaned_data["assignee_location"].values()) if form.cleaned_data["assignee_location"] else ""
            time_taken = time() - t
            return render(request, "main/result.html", 
                {"patents": patents, "time_taken": time_taken, "patents_count": patents_count,
                    "inventor_circle": inventor_circle, "assignee_circle": assignee_circle})
    else:
        form = MainForm()
    return render(request, "main/index.html", {"form": form})
