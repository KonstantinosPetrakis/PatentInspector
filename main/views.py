import json

from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from main.forms import *
from main.models import *


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():
            # Store the ids of the patents that match the query in the session
            request.session.flush()

            if settings.DEPLOYED and (patent_count := Patent.filter(form.cleaned_data).distinct("id").count()) < 30000:
                patent_ids = list(
                    Patent.filter(form.cleaned_data)
                    .distinct("id")
                    .values_list("id", flat=True)
                )
                request.session["form_data"] = json.dumps(
                    form.cleaned_data, cls=DjangoJSONEncoder
                )
                request.session["patent_ids"] = json.dumps(patent_ids)
                return render(request, "main/results.html")
            else:
                form.add_error(
                    None,
                    f"We are sorry but we do not have the capacity to process your query " \
                    f"of {patent_count} patents. Please try a more specific query."
                )
    else:
        form = MainForm()
    return render(request, "main/index.html", {"form": form})
