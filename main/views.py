from django.shortcuts import render
from main.forms import *
from main.models import *
from django.core.serializers.json import DjangoJSONEncoder
import json


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():
            # Store the ids of the patents that match the query in the session
            request.session.flush()
            patent_ids = list(Patent.filter(form.cleaned_data).distinct("id").values_list("id", flat=True))
            request.session["form_data"] = json.dumps(form.cleaned_data, cls=DjangoJSONEncoder)
            request.session["patent_ids"] = json.dumps(patent_ids)
            return render(request, "main/results.html")
    else:
        form = MainForm()
    return render(request, "main/index.html", {"form": form})
