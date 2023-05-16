from django.shortcuts import render
from main.forms import *
from main.models import *
from django.core.serializers.json import DjangoJSONEncoder
import json


def index(request):
    if request.method == "POST":
        form = MainForm(request=request)
        if form.is_valid():
            # Store the data in the session for later use (e.g export, pagination, ...)
            request.session["form_data"] = json.dumps(form.cleaned_data, cls=DjangoJSONEncoder)
    
            return render(request, "main/results.html")
    else:
        form = MainForm(request=request)
    return render(request, "main/index.html", {"form": form})
