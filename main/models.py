from django.db import models
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.conf import settings


def get_help_text(field):
    with open(f"{settings.BASE_DIR}/main/help_texts/patent/{field}.html", "r") as f:
        return mark_safe(f.read())


class CPCSection(models.Model):
    section = models.CharField(primary_key=True, max_length=100, help_text="The section of the CPC classification. E.g 'A'")
    title = models.TextField(help_text="The title of the section. E.g 'Human Necessities'")


class CPCClass(models.Model):
    section = models.ForeignKey(CPCSection, on_delete=models.PROTECT, related_name="classes")
    _class = models.CharField("class", primary_key=True, max_length=100, help_text="The class of the CPC classification. E.g 'A63'")
    title = models.TextField(help_text="The title of the class. E.g 'sports; games; amusements'")


class CPCSubclass(models.Model):
    _class = models.ForeignKey(CPCClass, on_delete=models.PROTECT, related_name="subclasses")
    cpc_subclass = models.CharField(primary_key=True, max_length=100, help_text="The subclass of the CPC classification. E.g 'A63B'")
    title = models.TextField(help_text="The title of the subclass. E.g 'apparatus for physical training, gymnastics, swimming, climbing, or fencing; ball games; training equipment'")


class CPCGroup(models.Model):
    cpc_subclass = models.ForeignKey(CPCSubclass, on_delete=models.PROTECT, related_name="groups")
    cpc_group = models.CharField(primary_key=True, max_length=100, help_text="The group of the CPC classification. E.g 'A63B71/146'")
    title = models.TextField(help_text="The title of the group. E.g 'Golf gloves'")


class Patent(models.Model):  
    type_choices = (
        ("utility", "Utility"),
        ("design", "Design"),
        ("plant", "Plant"),
        ("reissue", "Reissue")
    )

    office_choices = (
        ("uspto", "USPTO"),
    )

    office = models.CharField(max_length=100, choices=office_choices, help_text="The office that granted the patent.")
    office_patent_id = models.CharField(max_length=100, help_text="The ID of the patent in the office's database.")
    type = models.CharField(max_length=100, choices=type_choices, help_text=get_help_text("patent_type"))
    cpc_subgroup = models.ForeignKey(CPCGroup, on_delete=models.PROTECT, help_text="The CPC subgroup of the patent.", related_name="patents")
    application_filled_date = models.DateField(help_text="The date when the application was filed.")
    granted_date = models.DateField(help_text="The date when the patent was granted.")
    title = models.TextField(help_text="The title of the patent.")
    abstract = models.TextField(help_text="The abstract text of the patent.")
    num_claims = models.IntegerField(help_text="The number of claims in the patent.")
    figures_count = models.IntegerField(help_text="The number of figures included with the patent.")
    num_sheets = models.IntegerField(help_text="The number of sheets included with the patent.")
    withdrawn = models.BooleanField(help_text="Whether the patent has been withdrawn, in other words if it is still valid.")
    

class PCTData(models.Model):
    pct_state_choices = (
        ("granted", "Granted"),
        ("application", "Application"),
    )

    patent = models.OneToOneField(Patent, primary_key=True, on_delete=models.PROTECT, related_name="pct_date")
    published_or_filled_date = models.DateField(help_text="The date when the patent was published or filed in the PCT database.")
    application_number = models.CharField(max_length=100, help_text="The application number of the patent in the PCT database.")
    filled_country = models.CharField(max_length=100, help_text="The country where the patent was filed in the PCT database.")
    granted = models.BooleanField(help_text="Whether the patent is granted or it's just an application.")


class Location(models.Model):
    country = models.CharField(max_length=100, help_text="The country of the location.")
    state = models.CharField(max_length=100, help_text="The state of the location.")
    city = models.CharField(max_length=100, help_text="The city of the location.")
    latitude = models.FloatField(help_text="The latitude of the location.")
    longitude = models.FloatField(help_text="The longitude of the location.")


class Inventor(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="inventors")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="inventors")
    first_name = models.CharField(max_length=100, help_text="The first name of the inventor.")
    last_name = models.CharField(max_length=100, help_text="The last name of the inventor.")
    male = models.BooleanField(null=True, help_text="Where the inventor is male, if false is female, if null then no gender attributed.")


class Assignee(models.Model):
    patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="assignees")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="assignees")
    first_name = models.CharField(null=True, max_length=100, help_text="The first name of the assignee if the assignee is an individual.")
    last_name = models.CharField(null=True, max_length=100, help_text="The last name of the assignee if the assignee is an individual.")
    organization = models.CharField(null=True, max_length=100, help_text="The organization name if the assignee is an organization.")


class PatentCitation(models.Model):
    citing_patent = models.ForeignKey(Patent, on_delete=models.PROTECT, related_name="citations")
    cited_patent = models.ForeignKey(Patent, on_delete=models.PROTECT, null=True, related_name="cited_by")
    citation_date = models.DateField(help_text="The date when the patent was cited.")
    record_name = models.CharField(max_length=100, null=True, blank=True, help_text="The name of the record.")
    cited_patent_number = models.CharField(null=True, max_length=100, help_text="The application number of the cited patent if it's not in the database.")
    cited_patent_country = models.CharField(null=True, max_length=100, help_text="The country of the cited patent if it's not in the database.")
