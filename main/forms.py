from django.utils.safestring import mark_safe
from django.conf import settings
from main.models import Patent
from django import forms
from main.form_utils import *


def get_help_text(field):
    with open(f"{settings.BASE_DIR}/main/help_texts/patent/{field}.html", "r") as f:
        return mark_safe(f.read())


class MainForm(forms.Form):
    template_name = "main_form.html"
    patent_office = EmptyChoiceField(choices=Patent.office_choices, help_text="The office that granted the patent.")
    patent_type = EmptyChoiceField(choices=Patent.type_choices, help_text=get_help_text("patent_type"))
    patent_application_filed_date = RangeDateField(help_text="The date when the application was filed.")
    patent_grant_date = RangeDateField(help_text="The date when the application was filed.")
    patent_claims_count = RangeField(min=0, max=200, help_text="The number of claims in the patent.")
    patent_sheets_count = RangeField(min=0, max=200, help_text="The number of sheets in the patent.")
    patent_withdrawn = forms.BooleanField(required=False, help_text="Whether the patent has been withdrawn.")
