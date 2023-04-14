from django.utils.safestring import mark_safe
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.conf import settings
from main.api import build_url
from django.db.models import Q
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
        super().__init__(*args, **kwargs)
        self.field_categories = {
            "Main Fields": [field for field in self.fields if field.startswith("patent_")],
            "CPC fields": [field for field in self.fields if field.startswith("cpc_")],
            "PCT fields": [field for field in self.fields if field.startswith("pct_")],
            "Inventor fields": [field for field in self.fields if field.startswith("inventor_")],
            "Assignee fields": [field for field in self.fields if field.startswith("assignee_")],
        }

    def query_patents(self):
        def exact_query(field, value):
            return Q(**{field: value}) if value else Q()

        def range_query(field, value):
            query = Q()
            if value:
                if value["min"]: query &= Q(**{f"{field}__gte": value["min"]})
                if value["max"]: query &= Q(**{f"{field}__lte": value["max"]})
            return query

        data = self.cleaned_data
        keywords = "|".join(data["patent_keywords"])

        patent_query = exact_query("office", data["patent_office"])
        patent_query &= exact_query("type", data["patent_type"])
        patent_query &= range_query("application_filed_date", data["patent_application_filed_date"])
        patent_query &= range_query("granted_date", data["patent_granted_date"])
        patent_query &= range_query("figures_count", data["patent_figures_count"])
        patent_query &= range_query("claims_count", data["patent_claims_count"])
        patent_query &= range_query("sheets_count", data["patent_sheets_count"])

        if data["patent_withdrawn"] is not None: patent_query &= Q(withdrawn=data["patent_withdrawn"])
        
        if data["patent_keywords"]: # design patents usually don't have abstracts and have really small titles, so full text search doesn't work well for them.
            if not data["patent_type"]: patent_query &= Q(search=keywords) | Q(title__iregex=keywords)
            elif data["patent_type"] == "design": patent_query &= Q(title__iregex=keywords)
            else: patent_query &= Q(search=keywords)

        cpc_query = Q()    
        # Remove redundant keywords from the lower levels of the hierarchy for each level.
        hierarchies = ["cpc_section", "cpc_class", "cpc_subclass", "cpc_group"]
        for level_index, level in enumerate(hierarchies): 
            for hierarchy_below in hierarchies[level_index+1:]:
                for key in data[level]:
                    data[hierarchy_below] = [keyword for keyword in data[hierarchy_below] if not keyword.startswith(key)]
        
        # Then create the query using like queries in the groups.
        if sections := data["cpc_section"]: cpc_query &= Q(cpc_groups__cpc_group__group__iregex=f"^({'|'.join(sections)})")
        if classes := data["cpc_class"]: cpc_query &= Q(cpc_groups__cpc_group__group__iregex=f"^({'|'.join(classes)})")
        if subclasses := data["cpc_subclass"]: cpc_query &= Q(cpc_groups__cpc_group__group__iregex=f"^({'|'.join(subclasses)})")
        if groups := data["cpc_group"]: cpc_query &= Q(cpc_groups__cpc_group__in=groups)
        
        pct_query = range_query("pct_data__published_or_filed_date", data["pct_application_date"])
        if data["pct_granted"] is not None: pct_query &= Q(pct_data__granted=data["pct_granted"])

        inventor_query = Q()
        if data["inventor_first_name"]: inventor_query &= Q(inventors__first_name__iregex=f"^({''.join(data['inventor_first_name'])})")
        if data["inventor_last_name"]: inventor_query &= Q(inventors__last_name__in=data['inventor_last_name'])
        if data["inventor_male"] is not None: inventor_query &= Q(inventors__male=data["inventor_male"])
        if location := data["inventor_location"]:inventor_query &= Q(inventors__location__point__distance_lte=(Point(location['lng'], location['lat']), D(m=location['radius'])))
        
        assignee_query = Q()
        if data["assignee_first_name"]: assignee_query &= Q(assignees__first_name__iregex=f"^({''.join(data['assignee_first_name'])})")
        if data["assignee_last_name"]: assignee_query &= Q(assignees__last_name__in=data['assignee_last_name'])
        if data["assignee_organization"]: assignee_query &= Q(assignees__organization__in=data['assignee_organization'])

        query = patent_query & cpc_query & pct_query & inventor_query & assignee_query
        return Patent.objects.filter(query).prefetch_related("cpc_groups__cpc_group", "pct_data", "inventors", "assignees", "inventors__location", "assignees__location")[:100]
    