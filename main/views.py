from django.contrib.postgres.aggregates import StringAgg
from django.db.models.functions import Concat, Cast
from django.db.models import CharField, Case, When, Value, F, Func
from django.shortcuts import render
from main.forms import *
from main.models import *
from time import time


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():
            inventor_circle = ",".join([str(val) for val in form.cleaned_data["inventor_location"].values()]) if form.cleaned_data["inventor_location"] else ""
            assignee_circle = ",".join(str(val) for val in form.cleaned_data["assignee_location"].values()) if form.cleaned_data["assignee_location"] else ""    
            patents_total_count = Patent.approximate_count()
            t = time()
            patents = form.query_patents()
            patents = patents.annotate(
                cpc_groups_groups=StringAgg("cpc_groups__cpc_group__group", delimiter=", ", distinct=True),
                pct_data_dates=StringAgg(Cast("pct_data__published_or_filed_date", CharField()), delimiter=", ", distinct=True),
                pct_data_granted=StringAgg(Cast("pct_data__granted", CharField()), delimiter=", ", distinct=True),
                inventor_names=StringAgg(Concat(F("inventors__first_name"), Value(" "), F("inventors__last_name")), delimiter=", ", distinct=True),
                inventor_points=StringAgg(Concat(Func("inventors__location__point", function="ST_X"), Value("|"), Func("inventors__location__point", function="ST_Y")), delimiter=","),
                assignee_names=StringAgg(Case(When(assignees__organization="", then=Concat(F("assignees__first_name"), Value(" "), F("assignees__last_name"))), default=F("assignees__organization")), delimiter=", ", distinct=True),
                assignee_points=StringAgg(Concat(Func("assignees__location__point", function="ST_X"), Value("|"), Func("assignees__location__point", function="ST_Y")), delimiter=","),
            )
            patents_count = len(patents)
            time_taken = time() - t 
            return render(request, "main/result.html", 
                {"patents": patents, "time_taken": time_taken, "patents_total_count": patents_total_count,
                    "inventor_circle": inventor_circle, "assignee_circle": assignee_circle,
                    "patents_count": patents_count})
    else:
        form = MainForm()
    return render(request, "main/index.html", {"form": form})
