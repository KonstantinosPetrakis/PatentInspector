from django.utils.safestring import mark_safe
from django.conf import settings
from main.api import build_url
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
    cpc_section = ChoiceKeywordsField(url=build_url(CPCSection), help_text="The section of the CPC classification. E.g 'A - HUMAN NECESSITIES'")
    cpc_class = ChoiceKeywordsField(url=build_url(CPCClass), help_text="The class of the CPC classification. E.g 'A01 - AGRICULTURE; FORESTRY; ANIMAL HUSBANDRY; HUNTING; TRAPPING; FISHING'")
    cpc_subclass = ChoiceKeywordsField(min_query_length=1, url=build_url(CPCSubclass), help_text="The subclass of the CPC classification. E.g 'A01B - SOIL WORKING IN AGRICULTURE OR FORESTRY; PARTS, DETAILS, OR ACCESSORIES OF AGRICULTURAL MACHINES OR IMPLEMENTS, IN GENERAL'")
    cpc_group = ChoiceKeywordsField(min_query_length=3, url=build_url(CPCGroup), help_text="The group of the CPC classification. E.g 'A01B1/00	Hand tools'")
    pct_application_date = RangeDateField(help_text="The date when the PCT application was filed. To retrieve all patents that have a PCT application you can add 2 dates that are really far apart effectively encompassing all PCT applications.")
    pct_granted = TriStateField(help_text="Whether the patent has been granted protection under the PCT.")
    inventor_location = RadiusField(help_text="The location of the inventor.")
    inventor_first_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Inventor, "first_name"), help_text="The first name of the inventor. All first names that start-with the given first name will be returned.")
    inventor_last_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Inventor, "last_name"), help_text="The last name of the inventor. The last name will be matched exactly, so if you want more variants you will have to select them.")
    inventor_male = TriStateField(help_text="Whether the inventor is male or not.")
    assignee_location = RadiusField(help_text="The location of the assignee.")
    assignee_first_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "first_name"), help_text="The first name name of the assignee if it is an individual. All first names that start-with the given first name will be returned.")
    assignee_last_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "last_name"), help_text="The last name of the assignee if it is an individual. The last name will be matched exactly, so if you want more variants you will have to select them.")
    assignee_organization = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "organization"), help_text="The name of the organization if the assignee is an organization.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_categories = {
            "Main Fields": [field for field in self.fields if field.startswith("patent_")],
            "CPC fields": [field for field in self.fields if field.startswith("cpc_")],
            "PCT fields": [field for field in self.fields if field.startswith("pct_")],
            "Inventor fields": [field for field in self.fields if field.startswith("inventor_")],
            "Assignee fields": [field for field in self.fields if field.startswith("assignee_")],
        }