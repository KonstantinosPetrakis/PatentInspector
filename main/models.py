from django.db.models import CharField, Case, When, Value, F, Q, Func
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.functions import Concat, Cast
from django.utils.safestring import mark_safe
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db import models
from postgres_copy import CopyManager
from django.conf import settings
from django.db import connection



def get_help_text(field):
    with open(f"{settings.BASE_DIR}/main/help_texts/patent/{field}.html", "r") as f:
        return mark_safe(f.read())


class CPCSection(models.Model):
    section = models.CharField(primary_key=True, max_length=100, help_text="The section of the CPC classification. E.g 'A'")
    title = models.TextField(help_text="The title of the section. E.g 'Human Necessities'")

    def __str__(self):
        return self.section


class CPCClass(models.Model):
    section = models.ForeignKey(CPCSection, on_delete=models.PROTECT, related_name="classes")
    _class = models.CharField("class", primary_key=True, max_length=100, help_text="The class of the CPC classification. E.g 'A63'")
    title = models.TextField(help_text="The title of the class. E.g 'sports; games; amusements'")

    def __str__(self):
        return self._class


class CPCSubclass(models.Model):
    _class = models.ForeignKey(CPCClass, on_delete=models.PROTECT, related_name="subclasses")
    subclass = models.CharField(primary_key=True, max_length=100, help_text="The subclass of the CPC classification. E.g 'A63B'")
    title = models.TextField(help_text="The title of the subclass. E.g 'apparatus for physical training, gymnastics, swimming, climbing, or fencing; ball games; training equipment'")

    def __str__(self):
        return self.subclass


class CPCGroup(models.Model):
    subclass = models.ForeignKey(CPCSubclass, on_delete=models.PROTECT, related_name="groups")
    group = models.CharField(primary_key=True, max_length=100, help_text="The group of the CPC classification. E.g 'A63B71/146'")
    title = models.TextField(help_text="The title of the group. E.g 'Golf gloves'")
    
    def __str__(self):
        return self.group


class Patent(models.Model):  
    type_choices = [
        ("utility", "Utility"),
        ("design", "Design"),
        ("plant", "Plant"),
        ("reissue", "Reissue"),
    ]

    office_choices = [
        ("USPTO", "USPTO"),
    ]

    office = models.CharField(max_length=100, choices=office_choices, help_text="The office that granted the patent.")
    office_patent_id = models.CharField(max_length=100, help_text="The ID of the patent in the office's database.")
    type = models.CharField(null=True, blank=True, max_length=100, choices=type_choices,help_text=get_help_text("patent_type"))
    application_filed_date = models.DateField(null=True, help_text="The date when the application was filed.")
    granted_date = models.DateField(help_text="The date when the patent was granted.")
    title = models.TextField(help_text="The title of the patent.")
    abstract = models.TextField(null=True, blank=True, help_text="The abstract text of the patent.")
    claims_count = models.IntegerField(help_text="The number of claims in the patent.")
    figures_count = models.IntegerField(null=True, help_text="The number of figures included with the patent.")
    sheets_count = models.IntegerField(null=True, help_text="The number of sheets included with the patent.")
    withdrawn = models.BooleanField(help_text="Whether the patent has been withdrawn, in other words if it hasn't lost its validity.")
    objects = CopyManager()

    def __str__(self):
        return f"{self.office} - {self.office_patent_id}"
    
    @staticmethod
    def approximate_count():
        cursor = connection.cursor()
        cursor.execute("SELECT reltuples FROM pg_class WHERE relname = %s", [Patent._meta.db_table])
        return int(cursor.fetchone()[0])

    @staticmethod
    def filter(data):
        def exact_query(field, value):
            return Q(**{field: value}) if value else Q()

        def range_query(field, value):
            query = Q()
            if value:
                if value["min"]: query &= Q(**{f"{field}__gte": value["min"]})
                if value["max"]: query &= Q(**{f"{field}__lte": value["max"]})
            return query        

        keywords = data["patent_keywords_logic"].join(data["patent_keywords"])

        patent_query = exact_query("office", data["patent_office"])
        patent_query &= exact_query("type", data["patent_type"])
        patent_query &= range_query("application_filed_date", data["patent_application_filed_date"])
        patent_query &= range_query("granted_date", data["patent_granted_date"])
        patent_query &= range_query("figures_count", data["patent_figures_count"])
        patent_query &= range_query("claims_count", data["patent_claims_count"])
        patent_query &= range_query("sheets_count", data["patent_sheets_count"])

        if data["patent_withdrawn"] is not None: patent_query &= Q(withdrawn=data["patent_withdrawn"])
        
        if data["patent_keywords"]:
            patent_query &= Q(title__iregex=f"({keywords})") | Q(abstract__iregex=f"({keywords})")

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
        if location := data["inventor_location"]: inventor_query &= Q(inventors__location__point__distance_lte=(Point(location['lng'], location['lat']), D(m=location['radius'])))
        
        assignee_query = Q()
        if data["assignee_first_name"]: assignee_query &= Q(assignees__first_name__iregex=f"^({''.join(data['assignee_first_name'])})")
        if data["assignee_last_name"]: assignee_query &= Q(assignees__last_name__in=data['assignee_last_name'])
        if data["assignee_organization"]: assignee_query &= Q(assignees__organization__in=data['assignee_organization'])
        if location := data["assignee_location"]: assignee_query &= Q(assignees__location__point__distance_lte=(Point(location['lng'], location['lat']), D(m=location['radius'])))
        
        query = patent_query & cpc_query & pct_query & inventor_query & assignee_query
                
        return Patent.objects.filter(query)

    @staticmethod
    def fetch_representation(patents):
        return patents.annotate(
            cpc_groups_groups=StringAgg("cpc_groups__cpc_group__group", delimiter=", ", distinct=True),
            pct_documents=StringAgg(Concat(
                Cast("pct_data__published_or_filed_date", CharField()),
                Case(When(pct_data__granted=True, then=Value(" - granted"))),
                Case(When(pct_data__granted=False, then=Value(" - not granted")))
            ), delimiter=", ", distinct=True),
            inventor_names=StringAgg(Concat(
                F("inventors__first_name"), Value(" "), F("inventors__last_name")
            ), delimiter=", ", distinct=True),
            inventor_points=StringAgg(Concat(
                Func("inventors__location__point", function="ST_X"), Value("|"),
                Func("inventors__location__point", function="ST_Y")
            ), delimiter=",", distinct=True),
            assignee_names=StringAgg(Case(When(assignees__organization="",
                then=Concat(F("assignees__first_name"), Value(" "), F("assignees__last_name"))),
                default=F("assignees__organization")
            ), delimiter=", ", distinct=True),
            assignee_points=StringAgg(Concat(
                Func("assignees__location__point", function="ST_X"), Value("|"),
                Func("assignees__location__point", function="ST_Y")
            ), delimiter=",", distinct=True),
        ).order_by("id")


class PatentCPCGroup(models.Model):
    class Meta:
        unique_together = ("patent", "cpc_group")

    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="cpc_groups")
    cpc_group = models.ForeignKey(CPCGroup, on_delete=models.PROTECT, related_name="patents")
    objects = CopyManager()


class PCTData(models.Model):
    pct_state_choices = (
        ("granted", "Granted"),
        ("application", "Application"),
    )

    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="pct_data")
    pct_id = models.CharField(max_length=100, help_text="The ID of the patent in the PCT database.")
    published_or_filed_date = models.DateField(help_text="The date when the patent was published or filed by the office.")
    filed_country = models.CharField(max_length=100, help_text="The country code where the patent was filed in the PCT database.")
    granted = models.BooleanField(help_text="Whether the patent is published and granted or it's just filed.")
    objects = CopyManager()
    

class Location(models.Model):
    country_code = models.CharField(null=True, max_length=100, help_text="The country of the location.")
    state = models.CharField(null=True, max_length=100, help_text="The state of the location.")
    city = models.CharField(null=True, max_length=100, help_text="The city of the location.")
    point = models.PointField(null=True, help_text="The point (lat and lon) of the location.")
    county_fips = models.IntegerField(null=True, help_text="The FIPS code of the county.")
    state_fips = models.IntegerField(null=True, help_text="The FIPS code of the state.")

    def __str__(self):
        if self.state: return f"{self.country_code} - {self.state} - {self.city}"
        return f"{self.country_code} - {self.city}"


class Inventor(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="inventors")
    location = models.ForeignKey(Location, null=True, on_delete=models.PROTECT, related_name="inventors")
    first_name = models.CharField(null=True, blank=True, max_length=100, help_text="The first name of the inventor.")
    last_name = models.CharField(null=True, blank=True, max_length=100, help_text="The last name of the inventor.")
    male = models.BooleanField(null=True, help_text="Whether the inventor is male, if false is female, if null then no gender attributed.")
    objects = CopyManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Assignee(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="assignees")
    location = models.ForeignKey(Location, null=True, on_delete=models.PROTECT, related_name="assignees")
    first_name = models.CharField(null=True, blank=True, max_length=100, help_text="The first name of the assignee if the assignee is an individual.")
    last_name = models.CharField(null=True, blank=True, max_length=100, help_text="The last name of the assignee if the assignee is an individual.")
    organization = models.CharField(null=True, max_length=100, help_text="The organization name if the assignee is an organization.")
    objects = CopyManager()

    def __str__(self):
        return self.organization if self.organization else f"{self.first_name} {self.last_name}" 


class PatentCitation(models.Model):
    citing_patent = models.ForeignKey(Patent, on_delete=models.PROTECT, null=True, related_name="citations")
    cited_patent = models.ForeignKey(Patent, on_delete=models.PROTECT, null=True, related_name="cited_by")
    citation_date = models.DateField(null=True, help_text="The date when the patent was cited.")
    record_name = models.CharField(max_length=150, null=True, blank=True, help_text="The name of the record.")
    cited_patent_number = models.CharField(null=True, max_length=100, help_text="The application number of the cited patent if it's not in the database.")
    cited_patent_country = models.CharField(null=True, max_length=100, help_text="The country code of the cited patent if it's not in the database.")
    objects = CopyManager()
    