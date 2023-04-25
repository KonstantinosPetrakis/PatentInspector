from django.utils.safestring import mark_safe

from main.api_urls import build_url
from django.conf import settings

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
    patent_keywords_logic = SwitchInputValuesField(choices=["|", " "], label="Include ALL patent keywords", help_text="Whether to use AND or OR when searching for keywords.") 
    patent_application_filed_date = RangeDateField(help_text="The date when the application was filed.")
    patent_granted_date = RangeDateField(help_text="The date when the protection was granted.")
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
    
    inventor_location = RadiusField(help_text="The location of the inventor. If there are multiple inventors, at least one of them must be in this location.")
    inventor_first_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Inventor, "first_name"), help_text="The first name of the inventor. If there are multiple inventors, at least one of them will have this first name.")
    inventor_last_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Inventor, "last_name"), help_text="The last name of the inventor. If there are multiple inventors, at least one of them must have this last name.")
    inventor_male = TriStateField(help_text="Whether the inventor is male or not. Currently there are no inventor records with gender declared.")
    
    assignee_location = RadiusField(help_text="The location of the assignee. If there are multiple assignees, at least one of them must be in this location.")
    assignee_first_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "first_name"), help_text="The first name name of the assignee if it is an individual. If there are multiple assignees, at least one of them will have this first name.")
    assignee_last_name = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "last_name"), help_text="The last name of the assignee if it is an individual. If there are multiple assignees, at least one of them must have this last name.")
    assignee_organization = ChoiceKeywordsField(min_query_length=2, url=build_url(Assignee, "organization"), help_text="The name of the organization if the assignee is an organization. If there are multiple assignees, at least one of them must have this name.")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        if self.request.method == "POST": super().__init__(self.request.POST, **kwargs)
        else: super().__init__(**kwargs)
        self.field_categories = {
            "Main Fields": [field for field in self.fields if field.startswith("patent_")],
            "CPC fields": [field for field in self.fields if field.startswith("cpc_")],
            "PCT fields": [field for field in self.fields if field.startswith("pct_")],
            "Inventor fields": [field for field in self.fields if field.startswith("inventor_")],
            "Assignee fields": [field for field in self.fields if field.startswith("assignee_")],
        }
