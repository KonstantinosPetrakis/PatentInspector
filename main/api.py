from django.http import JsonResponse
from main.models import *


def cpc_sections(request, query=""):
    return JsonResponse(list(CPCSection.objects.filter(section__icontains=query).values()), safe=False)