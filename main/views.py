from django.shortcuts import render
from main.forms import *


def index(request):
    if request.method == "POST":
        form = MainForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
    else:
        form = MainForm()

    return render(request, "main/index.html", {"form": form})
