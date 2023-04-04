from django.utils.safestring import mark_safe
from django.conf import settings
from django.urls import reverse_lazy as reverse
from main.form_utils import *
from main.models import *
from django import forms


def get_help_text(field):
    with open(f"{settings.BASE_DIR}/main/help_texts/patent/{field}.html", "r") as f:
        return mark_safe(f.read())


class MainForm(forms.Form):
    template_name = "main/main_form.html"
    patent_office = EmptyChoiceField(choices=Patent.office_choices, help_text="The office that granted the patent.")
    patent_type = EmptyChoiceField(choices=Patent.type_choices, help_text=get_help_text("patent_type"))
    patent_keywords = KeywordField(help_text="Keywords to search for in the patent's title and abstract.")
    patent_application_filed_date = RangeDateField(help_text="The date when the application was filed.")
    patent_grant_date = RangeDateField(help_text="The date when the application was filed.")
    patent_figures_count = RangeField(min=0, max=200, help_text="The number of figures in the patent.")
    patent_claims_count = RangeField(min=0, max=200, help_text="The number of claims in the patent.")
    patent_sheets_count = RangeField(min=0, max=200, help_text="The number of sheets in the patent.")
    patent_withdrawn = TriStateField(help_text="Whether the patent has been withdrawn.")
    cpc_section = ChoiceKeywordsInputField(url=reverse("cpc-sections"), help_text="The section of the CPC classification. E.g 'A - HUMAN NECESSITIES'")
    cpc_class = forms.CharField()
    cpc_subclass = forms.CharField()
    cpc_group = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_categories = {
            "Main Fields": [field for field in self.fields if field.startswith("patent_")],
            "CPC fields": [field for field in self.fields if field.startswith("cpc_")],
        }