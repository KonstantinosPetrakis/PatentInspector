from typing import List, Tuple
import contextlib
import threading
import os
import secrets

from django.db.backends.postgresql.psycopg_any import NumericRange, DateRange
from django.db.models import Value, F, Q, Func, Q, OuterRef, Exists, TextField, fields
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields import ArrayField, IntegerRangeField, DateRangeField
from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import send_mail
from django.db.models.functions import Concat, Substr
from django.core.exceptions import ValidationError
from django.db.models.functions import Substr
from django.db.models.aggregates import Count
from django.contrib.gis.db import models
from django.db import connection
from django.conf import settings
from postgres_copy import CopyManager

from main.helpers import *


# ----- Analysis Related Models Begin -----


def get_coordinates(field):
    """
    This function creates a query to get the coordinates of a point field.
    """

    return {
        "lng": Func(field, function="ST_X", output_field=fields.FloatField()),
        "lat": Func(field, function="ST_Y", output_field=fields.FloatField()),
    }


def append_title_to_cpc_entity(results: List[Tuple]) -> List[List]:
    """
    This function appends the title to the cpc entity.

    Args:
        results (List[Tuple]): The tabular data that includes a cpc entity.

    Returns:
        List[Tuple]: The updated tabular data.
    """

    cpc_entities = {
        "CPC Section": CPCSection,
        "CPC Class": CPCClass,
        "CPC Subclass": CPCSubclass,
        "CPC Group": CPCGroup,
    }

    fields = results[0]
    cpc_entity = next(cpc for cpc in cpc_entities if cpc in fields)
    cpc_entity_model = cpc_entities[cpc_entity]
    cpc_entity_index = fields.index(cpc_entity)

    distinct_cpc_entity_values = set(
        [result[cpc_entity_index] for result in results[1:]]
    )

    cpc_entity_titles = {
        row["pk"]: row["title"]
        for row in cpc_entity_model.objects.filter(
            pk__in=distinct_cpc_entity_values
        ).values("pk", "title")
    }

    return [fields] + [
        [
            cell if i != cpc_entity_index else f"{cell} - {cpc_entity_titles[cell]}"
            for i, cell in enumerate(row)
        ]
        for row in results[1:]
    ]


def create_token():
    return secrets.token_hex(4)


class CPCSection(models.Model):
    section = models.CharField(
        primary_key=True,
        max_length=100,
    )
    title = models.TextField()

    def __str__(self):
        return self.section


class CPCClass(models.Model):
    section = models.ForeignKey(
        CPCSection, on_delete=models.PROTECT, related_name="classes"
    )
    _class = models.CharField(
        "class",
        primary_key=True,
        max_length=100,
    )
    title = models.TextField()

    def __str__(self):
        return self._class


class CPCSubclass(models.Model):
    _class = models.ForeignKey(
        CPCClass, on_delete=models.PROTECT, related_name="subclasses"
    )
    subclass = models.CharField(
        primary_key=True,
        max_length=100,
    )
    title = models.TextField()

    def __str__(self):
        return self.subclass


class CPCGroup(models.Model):
    subclass = models.ForeignKey(
        CPCSubclass, on_delete=models.PROTECT, related_name="groups"
    )
    group = models.CharField(
        primary_key=True,
        max_length=100,
    )
    title = models.TextField()

    def __str__(self):
        return self.group


class Patent(models.Model):
    type_choices = [
        ("utility", "Utility"),
        ("design", "Design"),
        ("plant", "Plant"),
        ("reissue", "Plant"),
        ("defensive publication", "Defensive Publication"),
    ]

    office_choices = [
        ("US", "US"),
    ]

    office = models.CharField(
        max_length=100,
        choices=office_choices,
    )
    office_patent_id = models.CharField(
        max_length=100,
    )
    type = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        choices=type_choices,
    )
    application_filed_date = models.DateField(
        null=True,
    )
    granted_date = models.DateField()
    title = models.TextField()
    abstract_processed = models.TextField(
        null=True,
        blank=True,
    )
    claims_count = models.IntegerField()
    figures_count = models.IntegerField(
        null=True,
    )
    sheets_count = models.IntegerField(
        null=True,
    )
    withdrawn = models.BooleanField()
    # Precomputed fields for optimization.
    granted_year = models.IntegerField(
        null=True,
        default=None,
    )
    application_year = models.IntegerField(
        null=True,
        default=None,
    )
    years_to_get_granted = models.FloatField(
        null=True,
        default=None,
    )
    title_processed = models.TextField(
        null=True,
        default=None,
    )
    title_word_count_without_processing = models.IntegerField(
        null=True,
        default=None,
    )
    title_word_count_with_processing = models.IntegerField(
        null=True,
        default=None,
    )
    abstract_word_count_without_processing = models.IntegerField(
        null=True,
        default=None,
    )
    abstract_word_count_with_processing = models.IntegerField(
        null=True,
        default=None,
    )
    cpc_groups_count = models.IntegerField(
        null=True,
        default=None,
    )
    assignee_count = models.IntegerField(
        null=True,
        default=None,
    )
    inventor_count = models.IntegerField(
        null=True,
        default=None,
    )
    incoming_citations_count = models.IntegerField(
        null=True,
        default=None,
    )
    outgoing_citations_count = models.IntegerField(
        null=True,
        default=None,
    )

    objects = CopyManager()

    @staticmethod
    def approximate_count() -> int:
        """
        This function will return the approximate count of the patents in the database.
        This is much faster than the default count function of Django ORM.
        Counts need sequential scans of the table, which is very slow.

        Returns:
            int: The approximate count of the patents in the database.
        """

        with connection.cursor() as curs:
            curs.execute(
                "SELECT reltuples FROM pg_class WHERE relname = %s",
                [Patent._meta.db_table],
            )
            return int(curs.fetchone()[0])

    @staticmethod
    def fetch_representation(patents: models.QuerySet) -> models.QuerySet:
        """
        This function will fetch the representation of the given patents.
        Essentially it will fetch all the related data of the patents in one query.
        Useful for exporting the data to excel or displaying summary data in the frontend.

        Args:
            patents (models.QuerySet): The patents to fetch the representation of.

        Returns:
            models.QuerySet: The patents with their representation.
        """

        return patents.annotate(
            cpc_groups_groups=StringAgg(
                "cpc_groups__cpc_group__group", delimiter=", ", distinct=True
            ),
            pct_documents=StringAgg(
                "pct_data__representation",
                delimiter=", ",
                distinct=True,
            ),
            inventor_names=StringAgg(
                Concat(
                    F("inventors__first_name"), Value(" "), F("inventors__last_name")
                ),
                delimiter=", ",
                distinct=True,
            ),
            inventor_points=StringAgg(
                Concat(
                    Func("inventors__location__point", function="ST_X"),
                    Value("|"),
                    Func("inventors__location__point", function="ST_Y"),
                ),
                delimiter=",",
                distinct=True,
            ),
            assignee_names=StringAgg(
                Concat(
                    F("assignees__first_name"),
                    Value(" "),
                    F("assignees__last_name"),
                    Value(" "),
                    F("assignees__organization"),
                ),
                delimiter=", ",
                distinct=True,
            ),
            assignee_points=StringAgg(
                Concat(
                    Func("assignees__location__point", function="ST_X"),
                    Value("|"),
                    Func("assignees__location__point", function="ST_Y"),
                ),
                delimiter=",",
                distinct=True,
            ),
        ).order_by("id")

    @staticmethod
    def fetch_minimal_representation(patents: models.QuerySet) -> models.QuerySet:
        return patents.order_by("id").values(
            "office",
            "office_patent_id",
            "type",
            "application_filed_date",
            "granted_date",
            "title",
            "abstract_processed",
            "claims_count",
            "figures_count",
            "sheets_count",
            "cpc_groups_count",
            "inventor_count",
            "assignee_count",
            "incoming_citations_count",
            "outgoing_citations_count",
            "withdrawn",
        )

    @staticmethod
    def applications_per_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("application_year")
            .annotate(count=Count("id"))
            .order_by("application_year")
            .values_list("application_year", "count")
        )
        data.insert(0, ["Year", "Count"])
        return data

    @staticmethod
    def granted_patents_per_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("granted_year")
            .annotate(count=Count("id"))
            .order_by("granted_year")
            .values_list("granted_year", "count")
        )
        data.insert(0, ["Year", "Count"])
        return data

    @staticmethod
    def granted_patents_per_type_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("granted_year", "type")
            .annotate(count=Count("id"))
            .order_by("granted_year", "type")
            .values_list("granted_year", "type", "count")
        )
        data.insert(0, ["Year", "Type", "Count"])
        return data

    @staticmethod
    def granted_patents_per_office_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("granted_year", "office")
            .annotate(count=Count("id"))
            .order_by("granted_year", "office")
            .values_list("granted_year", "office", "count")
        )
        data.insert(0, ["Year", "Office", "Count"])
        return data

    @staticmethod
    def pct_protected_patents_per_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.filter(pct_data__granted=True)
            .values("granted_year")
            .annotate(count=Count("id"))
            .order_by("granted_year")
            .values_list("granted_year", "count")
        )
        data.insert(0, ["Year", "Count"])
        return data

    @staticmethod
    def granted_patents_per_cpc_year(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
            .filter(~Q(cpc_section=""))
            .values("granted_year", "cpc_section")
            .annotate(count=Count("id"))
            .order_by("granted_year", "cpc_section")
            .values_list("granted_year", "cpc_section", "count")
        )
        data.insert(0, ["Year", "CPC Section", "Count"])
        return append_title_to_cpc_entity(data)

    @staticmethod
    def citations_made_per_year(patent_ids: list) -> List[Tuple]:
        data = list(
            PatentCitation.objects.filter(citing_patent_id__in=patent_ids)
            .values("citation_year")
            .annotate(count=Count("citing_patent_id"))
            .order_by("citation_year")
            .values_list("citation_year", "count")
        )
        data.insert(0, ["Year", "Count"])
        return data

    @staticmethod
    def citations_received_per_year(patent_ids: list) -> List[Tuple]:
        data = list(
            PatentCitation.objects.filter(cited_patent_id__in=patent_ids)
            .values("citation_year")
            .annotate(count=Count("cited_patent_id"))
            .order_by("citation_year")
            .values_list("citation_year", "count")
        )
        data.insert(0, ["Year", "Count"])
        return data

    @staticmethod
    def pct_distribution(patents: models.QuerySet) -> List[Tuple]:
        return [
            ["PCT Status", "Count"],
            ["Not Applied", Patent.pct_not_applied(patents)],
            ["Not Granted", Patent.pct_not_granted(patents)],
            ["Granted", Patent.pct_granted(patents)],
        ]

    @staticmethod
    def pct_not_applied(patents: models.QuerySet) -> int:
        return patents.filter(pct_data__isnull=True).count()

    @staticmethod
    def pct_not_granted(patents: models.QuerySet) -> int:
        return (
            patents.annotate(
                all_not_granted=~Exists(
                    PCTData.objects.filter(Q(granted=True), patent_id=OuterRef("pk"))
                )
            )
            .filter(all_not_granted=True, pct_data__isnull=False)
            .count()
        )

    @staticmethod
    def pct_granted(patents: models.QuerySet) -> int:
        return patents.filter(pct_data__granted=True).count()

    @staticmethod
    def types(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("type")
            .annotate(count=Count("id"))
            .order_by("count")
            .values_list("type", "count")
        )
        data.insert(0, ["Type", "Count"])
        return data

    @staticmethod
    def offices(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.values("office")
            .annotate(count=Count("id"))
            .order_by("count")
            .values_list("office", "count")
        )
        data.insert(0, ["Office", "Count"])
        return data

    @staticmethod
    def top_10_inventors(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(
                inventor=Concat(
                    "inventors__first_name", Value(" "), "inventors__last_name"
                )
            )
            .filter(~Q(inventor__iregex=r"^\s*$"))
            .values("inventor")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
            .values_list("inventor", "count")
        )
        data.insert(0, ["Inventor", "Count"])
        return data

    @staticmethod
    def inventor_locations(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(
                **get_coordinates("inventors__location__point"),
                location=Concat(
                    "inventors__location__country_code",
                    Value(" - "),
                    "inventors__location__city",
                ),
            )
            .filter(lat__isnull=False, lng__isnull=False)
            .values("lat", "lng", "location")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("lat", "lng", "location", "count")
        )
        data.insert(0, ["Lat", "Lng", "Location", "Count"])
        return data

    @staticmethod
    def top_10_assignees(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(
                assignee=Concat(
                    "assignees__first_name",
                    Value(" "),
                    "assignees__last_name",
                    Value(" "),
                    "assignees__organization",
                )
            )
            .filter(~Q(assignee__iregex=r"^\s*$"))
            .values("assignee")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
            .values_list("assignee", "count")
        )
        data.insert(0, ["Assignee", "Count"])
        return data

    @staticmethod
    def corporation_assignees_count(patents: models.QuerySet) -> int:
        return patents.filter(assignees__is_organization=True).count()

    @staticmethod
    def individual_assignees_count(patents: models.QuerySet) -> int:
        return patents.filter(assignees__is_organization=False).count()

    @staticmethod
    def assignee_type(patents: models.QuerySet) -> List[Tuple]:
        return [
            ["Assignee Type", "Count"],
            ["Corporation", Patent.corporation_assignees_count(patents)],
            ["Individual", Patent.individual_assignees_count(patents)],
        ]

    @staticmethod
    def assignee_locations(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(
                **get_coordinates("assignees__location__point"),
                location=Concat(
                    "assignees__location__country_code",
                    Value(" - "),
                    "assignees__location__city",
                ),
            )
            .filter(lat__isnull=False, lng__isnull=False)
            .values("lat", "lng", "location")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("lat", "lng", "location", "count")
        )
        data.insert(0, ["Lat", "Lng", "Location", "Count"])
        return data

    @staticmethod
    def cpc_sections(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
            .filter(~Q(cpc_section=""))
            .values("cpc_section")
            .annotate(count=Count("id"))
            .order_by("-count")
            .values_list("cpc_section", "count")
        )
        data.insert(0, ["CPC Section", "Count"])
        return append_title_to_cpc_entity(data)

    @staticmethod
    def top_5_cpc_classes(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(cpc_class=Substr("cpc_groups__cpc_group", 1, 3))
            .filter(~Q(cpc_class=""))
            .values("cpc_class")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
            .values_list("cpc_class", "count")
        )
        data.insert(0, ["CPC Class", "Count"])
        return append_title_to_cpc_entity(data)

    @staticmethod
    def top_5_cpc_subclasses(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.annotate(cpc_subclass=Substr("cpc_groups__cpc_group", 1, 4))
            .filter(~Q(cpc_subclass=""))
            .values("cpc_subclass")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
            .values_list("cpc_subclass", "count")
        )
        data.insert(0, ["CPC Subclass", "Count"])
        return append_title_to_cpc_entity(data)

    @staticmethod
    def top_5_cpc_groups(patents: models.QuerySet) -> List[Tuple]:
        data = list(
            patents.filter(cpc_groups__cpc_group__isnull=False)
            .values("cpc_groups__cpc_group")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
            .values_list("cpc_groups__cpc_group", "count")
        )
        data.insert(0, ["CPC Group", "Count"])
        return append_title_to_cpc_entity(data)


class PatentCPCGroup(models.Model):
    class Meta:
        unique_together = ("patent", "cpc_group")

    patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, related_name="cpc_groups"
    )
    cpc_group = models.ForeignKey(
        CPCGroup, on_delete=models.PROTECT, related_name="patents"
    )
    objects = CopyManager()


class PCTData(models.Model):
    pct_state_choices = (
        ("granted", "Granted"),
        ("application", "Application"),
    )

    patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, related_name="pct_data"
    )
    pct_id = models.CharField(
        max_length=100,
    )
    published_or_filed_date = models.DateField()
    filed_country = models.CharField(
        max_length=100,
    )
    granted = models.BooleanField()
    # Precomputed fields for optimization.
    representation = models.CharField(
        null=True,
        max_length=300,
    )
    objects = CopyManager()


class Location(models.Model):
    country_code = models.CharField(
        null=True,
        max_length=100,
    )
    state = models.CharField(
        null=True,
        max_length=100,
    )
    city = models.CharField(
        null=True,
        max_length=100,
    )
    point = models.PointField(
        null=True,
    )
    county_fips = models.IntegerField(
        null=True,
    )
    state_fips = models.IntegerField(
        null=True,
    )

    def __str__(self):
        if self.state:
            return f"{self.country_code} - {self.state} - {self.city}"
        return f"{self.country_code} - {self.city}"


class Inventor(models.Model):
    patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, related_name="inventors"
    )
    location = models.ForeignKey(
        Location, null=True, on_delete=models.PROTECT, related_name="inventors"
    )
    first_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    last_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    objects = CopyManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Assignee(models.Model):
    patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, related_name="assignees"
    )
    location = models.ForeignKey(
        Location, null=True, on_delete=models.PROTECT, related_name="assignees"
    )
    first_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    last_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
    )
    organization = models.CharField(
        null=True,
        max_length=100,
    )
    # Precomputed fields for optimization.
    is_organization = models.BooleanField(
        null=True,
        default=None,
    )
    objects = CopyManager()

    def __str__(self):
        return (
            self.organization
            if self.organization
            else f"{self.first_name} {self.last_name}"
        )


class PatentCitation(models.Model):
    patent_annotation = {
        "patent": Concat(
            F("cited_patent__office"),
            F("cited_patent__office_patent_id"),
            Value(" - "),
            F("cited_patent__title"),
            output_field=TextField(),
        )
    }

    citing_patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, null=True, related_name="citations"
    )
    cited_patent = models.ForeignKey(
        Patent, on_delete=models.PROTECT, null=True, related_name="cited_by"
    )
    citation_date = models.DateField(
        null=True,
    )
    cited_patent_number = models.CharField(
        null=True,
        max_length=100,
    )
    cited_patent_office = models.CharField(
        null=True,
        max_length=100,
    )
    # Precomputed fields for optimization.
    citation_year = models.IntegerField(
        null=True,
        default=None,
    )
    objects = CopyManager()

    @staticmethod
    def local_network_graph(local_network_ids: list) -> list:
        return list(
            PatentCitation.objects.filter(id__in=local_network_ids)
            .annotate(
                citing_patent_code=Concat(
                    "citing_patent__office", "citing_patent__office_patent_id"
                ),
                cited_patent_code=Concat(
                    "cited_patent__office", "cited_patent__office_patent_id"
                ),
            )
            .values(
                "citing_patent_id",
                "citing_patent_code",
                "citing_patent__title",
                "citing_patent__granted_date",
                "cited_patent_id",
                "cited_patent_code",
                "cited_patent__title",
                "cited_patent__granted_date",
            )
        )

    @staticmethod
    def most_cited_patents_local(local_network_ids: list) -> List[Tuple]:
        data = list(
            PatentCitation.objects.filter(id__in=local_network_ids)
            .values("cited_patent_id")
            .annotate(
                **PatentCitation.patent_annotation, count=Count("cited_patent_id")
            )
            .order_by("-count")[:10]
            .values_list("patent", "count")
        )
        data.insert(0, ["Patent", "Count"])
        return data

    @staticmethod
    def most_cited_patents_global(patent_ids: list) -> List[Tuple]:
        data = list(
            PatentCitation.objects.filter(
                Q(citing_patent_id__in=patent_ids) | Q(cited_patent_id__in=patent_ids)
            )
            .values("cited_patent_id")
            .annotate(
                **PatentCitation.patent_annotation, count=Count("cited_patent_id")
            )
            .order_by("-count")[:10]
            .values_list("patent", "count")
        )
        data.insert(0, ["Patent", "Count"])
        return data


# ----- Analysis Related Models End -----

# ----- Application Related Models And Validators Begin -----


def validate_cpc_sections(values):
    for value in values:
        if not CPCSection.objects.filter(section=value).exists():
            raise ValidationError(f"{value} is not a valid CPC section.")


def validate_cpc_classes(values):
    for value in values:
        if not CPCClass.objects.filter(_class=value).exists():
            raise ValidationError(f"{value} is not a valid CPC class.")


def validate_cpc_subclasses(values):
    for value in values:
        if not CPCSubclass.objects.filter(subclass=value).exists():
            raise ValidationError(f"{value} is not a valid CPC subclass.")


def validate_cpc_groups(values):
    for value in values:
        if not CPCGroup.objects.filter(group=value).exists():
            raise ValidationError(f"{value} is not a valid CPC group.")


class User(AbstractBaseUser):
    email = models.EmailField(
        unique=True, error_messages={"unique": "A user with that email already exists."}
    )
    wants_emails = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["password"]


class ResetPasswordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, default=create_token)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        getting_created = False
        if not self.pk:
            getting_created = True
        super().save(*args, **kwargs)

        if getting_created:
            threading.Thread(
                target=lambda: send_mail(
                    subject="PatentAnalyzer: Reset Password",
                    message=f"Your reset password token is {self.token}. It will expire in 5 minutes.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[self.user.email],
                )
            ).start()


class Report(models.Model):
    # Meta
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reports")
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_analysis_started = models.DateTimeField(null=True, blank=True)
    datetime_analysis_ended = models.DateTimeField(null=True, blank=True)
    executed_successfully = models.BooleanField(null=True, blank=True)
    status = models.CharField(
        choices=(
            ("idle", "Idle"),
            ("waiting_for_analysis", "Waiting For Execute"),
            ("waiting_for_topic_analysis", "Waiting For Topic Analysis"),
        ),
        max_length=100,
        default="waiting_for_analysis",
    )
    # Optimization
    patent_ids = ArrayField(
        models.IntegerField(),
        null=True,
        blank=True,
    )
    # Filters
    patent_office = models.CharField(
        choices=Patent.office_choices,
        max_length=100,
        null=True,
        blank=True,
    )
    patent_type = models.CharField(
        choices=Patent.type_choices,
        max_length=100,
        null=True,
        blank=True,
    )
    patent_keywords = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    patent_keywords_logic = models.CharField(
        choices=(("&", "and"), ("|", "or")),
        max_length=1,
        null=True,
        blank=True,
        default="&",
    )
    patent_application_filed_date = DateRangeField(null=True, blank=True)
    patent_granted_date = DateRangeField(null=True, blank=True)
    patent_figures_count = IntegerRangeField(null=True, blank=True)
    patent_claims_count = IntegerRangeField(null=True, blank=True)
    patent_sheets_count = IntegerRangeField(null=True, blank=True)
    patent_withdrawn = models.BooleanField(null=True, blank=True)

    cpc_section = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
        validators=[validate_cpc_sections],
    )
    cpc_class = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
        validators=[validate_cpc_classes],
    )
    cpc_subclass = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    cpc_group = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
        validators=[validate_cpc_groups],
    )

    pct_application_date = DateRangeField(null=True, blank=True)
    pct_granted = models.BooleanField(null=True, blank=True)

    inventor_first_name = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    inventor_last_name = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    inventor_location = models.JSONField(null=True, blank=True)

    assignee_first_name = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    assignee_last_name = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    assignee_organization = ArrayField(
        models.CharField(max_length=100),
        null=True,
        blank=True,
    )
    assignee_location = models.JSONField(null=True, blank=True)

    def get_patents(self):
        if self.patent_ids:
            return Patent.objects.filter(id__in=self.patent_ids).order_by("id")

        patent_query = exact_query("office", self.patent_office)
        patent_query &= exact_query("type", self.patent_type)
        patent_query &= exact_query("withdrawn", self.patent_withdrawn)
        patent_query &= range_query(
            "application_filed_date", self.patent_application_filed_date
        )
        patent_query &= exact_query("patent_withdrawn", self.patent_withdrawn)
        patent_query &= range_query("granted_date", self.patent_granted_date)
        patent_query &= range_query("figures_count", self.patent_figures_count)
        patent_query &= range_query("claims_count", self.patent_claims_count)
        patent_query &= range_query("sheets_count", self.patent_sheets_count)
        if self.patent_keywords:
            # Keywords must be full words e.g 'cat' shouldn't be matched in 'category'
            keywords = self.patent_keywords_logic.join(
                [f"(\\y{keyword}\\y)" for keyword in self.patent_keywords]
            )
            patent_query &= Q(title_processed__iregex=keywords) | Q(
                abstract_processed__iregex=keywords
            )

        cpc_query = list_iregex_query("cpc_groups__cpc_group__group", self.cpc_section)
        cpc_query &= list_iregex_query("cpc_groups__cpc_group__group", self.cpc_class)
        cpc_query &= list_iregex_query(
            "cpc_groups__cpc_group__group", self.cpc_subclass
        )
        cpc_query &= list_iregex_query("cpc_groups__cpc_group__group", self.cpc_group)

        pct_query = range_query(
            "pct_data__published_or_filed_date", self.pct_application_date
        )
        pct_query &= exact_query("pct_data__granted", self.pct_granted)

        inventor_query = list_iregex_query(
            "inventors__first_name", self.inventor_first_name
        )
        inventor_query &= list_iregex_query(
            "inventors__last_name", self.inventor_last_name
        )
        inventor_query &= location_query(
            "inventors__location__point", self.inventor_location
        )

        assignee_query = list_iregex_query(
            "assignees__first_name", self.assignee_first_name
        )
        assignee_query &= list_iregex_query(
            "assignees__last_name", self.assignee_last_name
        )
        assignee_query &= list_iregex_query(
            "assignees__organization", self.assignee_organization
        )
        assignee_query &= location_query(
            "assignees__location__point", self.assignee_location
        )

        return (
            Patent.objects.filter(
                patent_query, cpc_query, pct_query, inventor_query, assignee_query
            )
            .distinct("id")
            .order_by("id")
        )

    @property
    def excel_file(self) -> str:
        return os.path.join(settings.BASE_DIR, f"main/excels/{self.id}.xlsx")

    @property
    def results_file(self) -> str:
        return os.path.join(settings.BASE_DIR, f"main/results/{self.id}.json")

    @property
    def results(self) -> Dict:
        try:
            with open(self.results_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @results.setter
    def results(self, results):
        if not os.path.exists(os.path.dirname(self.results_file)):
            os.makedirs(os.path.dirname(self.results_file))

        with open(self.results_file, "w") as f:
            json.dump(results, f, default=str)

    def delete(self, *args, **kwargs):
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.excel_file)
            os.remove(self.results_file)

        super().delete(*args, **kwargs)

    @property
    def filters(self):
        def cast_value(value):
            value_type = type(value)
            if value_type == list:
                return ", ".join(value)
            elif value_type == dict:
                s = ""
                for key, value in value.items():
                    s += f"{key}: {value}, "
                return s[:-2]
            elif value_type in [NumericRange, DateRange]:
                return f"{value.lower} - {value.upper}"
            elif value_type == bool:
                return "Yes" if value else "No"
            elif value == "|":
                return "at least one of"
            return value

        filters = (
            Report.objects.filter(id=self.id)
            .values(
                "patent_office",
                "patent_type",
                "patent_keywords",
                "patent_keywords_logic",
                "patent_application_filed_date",
                "patent_granted_date",
                "patent_figures_count",
                "patent_claims_count",
                "patent_sheets_count",
                "patent_withdrawn",
                "cpc_section",
                "cpc_class",
                "cpc_subclass",
                "cpc_group",
                "pct_application_date",
                "pct_granted",
                "inventor_first_name",
                "inventor_last_name",
                "inventor_location",
                "assignee_first_name",
                "assignee_last_name",
                "assignee_organization",
                "assignee_location",
            )
            .first()
        )

        return {
            name.replace("_", " ").title(): cast_value(value)
            for name, value in filters.items()
            if value is not None
            and value != ""
            and value != []
            and value != "&"
        }


# ----- Application Related Models And Validators -----
