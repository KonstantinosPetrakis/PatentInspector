from django.db.models import Value, F, Q, Func, Q, OuterRef, Exists, TextField, fields
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.functions import Concat, Cast, Substr
from django.db.models.functions import Substr
from django.db.models.aggregates import Count
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db import models
from django.db import connection
from postgres_copy import CopyManager

from main.form_utils import get_help_text


def get_coordinates(field):
    """
    This function creates a query to get the coordinates of a point field.
    """

    return {
        "lng": Func(field, function="ST_X", output_field=fields.FloatField()),
        "lat": Func(field, function="ST_Y", output_field=fields.FloatField()),
    }


class CPCSection(models.Model):
    section = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="The section of the CPC classification. E.g 'A'",
    )
    title = models.TextField(
        help_text="The title of the section. E.g 'Human Necessities'"
    )

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
        help_text="The class of the CPC classification. E.g 'A63'",
    )
    title = models.TextField(
        help_text="The title of the class. E.g 'sports; games; amusements'"
    )

    def __str__(self):
        return self._class


class CPCSubclass(models.Model):
    _class = models.ForeignKey(
        CPCClass, on_delete=models.PROTECT, related_name="subclasses"
    )
    subclass = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="The subclass of the CPC classification. E.g 'A63B'",
    )
    title = models.TextField(
        help_text="The title of the subclass. E.g 'apparatus for physical training, gymnastics, swimming, climbing, or fencing; ball games; training equipment'"
    )

    def __str__(self):
        return self.subclass


class CPCGroup(models.Model):
    subclass = models.ForeignKey(
        CPCSubclass, on_delete=models.PROTECT, related_name="groups"
    )
    group = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="The group of the CPC classification. E.g 'A63B71/146'",
    )
    title = models.TextField(help_text="The title of the group. E.g 'Golf gloves'")

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
        help_text="The office that granted the patent.",
    )
    office_patent_id = models.CharField(
        max_length=100, help_text="The ID of the patent in the office's database."
    )
    type = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        choices=type_choices,
        help_text=get_help_text("patent_type"),
    )
    application_filed_date = models.DateField(
        null=True, help_text="The date when the application was filed."
    )
    granted_date = models.DateField(help_text="The date when the patent was granted.")
    title = models.TextField(help_text="The title of the patent.")
    abstract_processed = models.TextField(
        null=True, blank=True, help_text="The abstract processed text of the patent."
    )
    claims_count = models.IntegerField(help_text="The number of claims in the patent.")
    figures_count = models.IntegerField(
        null=True, help_text="The number of figures included with the patent."
    )
    sheets_count = models.IntegerField(
        null=True, help_text="The number of sheets included with the patent."
    )
    withdrawn = models.BooleanField(
        help_text="Whether the patent has been withdrawn, in other words if it hasn't lost its validity."
    )
    # Precomputed fields for optimization.
    granted_year = models.IntegerField(
        null=True, default=None, help_text="The year when the patent was granted."
    )
    application_year = models.IntegerField(
        null=True, default=None, help_text="The year when the application was filed."
    )
    years_to_get_granted = models.FloatField(
        null=True,
        default=None,
        help_text="The number of years it took for the patent to get granted.",
    )
    title_processed = models.TextField(
        null=True, default=None, help_text="The processed title of the patent."
    )
    title_word_count_without_processing = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of words in the title of the patent without processing.",
    )
    title_word_count_with_processing = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of words in the title of the patent with processing.",
    )
    abstract_word_count_without_processing = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of words in the abstract of the patent without processing.",
    )
    abstract_word_count_with_processing = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of words in the abstract of the patent with processing.",
    )
    cpc_groups_count = models.IntegerField(
        null=True, default=None, help_text="The number of CPC groups in the patent."
    )
    assignee_count = models.IntegerField(
        null=True, default=None, help_text="The number of assignees in the patent."
    )
    inventor_count = models.IntegerField(
        null=True, default=None, help_text="The number of inventors in the patent."
    )
    incoming_citations_count = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of incoming citations of the patent.",
    )
    outgoing_citations_count = models.IntegerField(
        null=True,
        default=None,
        help_text="The number of outgoing citations of the patent.",
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
                "SELECT reltuples FROM pg_class WHERE relname = %s", [Patent._meta.db_table]
            )
            return int(curs.fetchone()[0])

    @staticmethod
    def filter(data: dict) -> models.QuerySet:
        """
        This function will filter the patents based on the given data from the main form.

        Args:
            data (dict): The data from the main form.

        Returns:
            models.QuerySet: The filtered patents.
        """

        def exact_query(field, value):
            return Q(**{field: value}) if value else Q()

        def range_query(field, value):
            query = Q()
            if value:
                if value["min"]:
                    query &= Q(**{f"{field}__gte": value["min"]})
                if value["max"]:
                    query &= Q(**{f"{field}__lte": value["max"]})
            return query

        keywords = data["patent_keywords_logic"].join(data["patent_keywords"])

        patent_query = exact_query("office", data["patent_office"])
        patent_query &= exact_query("type", data["patent_type"])
        patent_query &= range_query(
            "application_filed_date", data["patent_application_filed_date"]
        )
        patent_query &= range_query("granted_date", data["patent_granted_date"])
        patent_query &= range_query("figures_count", data["patent_figures_count"])
        patent_query &= range_query("claims_count", data["patent_claims_count"])
        patent_query &= range_query("sheets_count", data["patent_sheets_count"])

        if data["patent_withdrawn"] is not None:
            patent_query &= Q(withdrawn=data["patent_withdrawn"])

        if data["patent_keywords"]:
            patent_query &= Q(title_processed__iregex=f"({keywords})") | Q(
                abstract_processed__iregex=f"({keywords})"
            )

        cpc_query = Q()
        # Remove redundant keywords from the lower levels of the hierarchy for each level.
        # For example if the user selected A01 we don't need to include A01B, A01C, etc.
        hierarchies = ["cpc_section", "cpc_class", "cpc_subclass", "cpc_group"]
        for level_index, level in enumerate(hierarchies):
            for hierarchy_below in hierarchies[level_index + 1 :]:
                for key in data[level]:
                    data[hierarchy_below] = [
                        keyword
                        for keyword in data[hierarchy_below]
                        if not keyword.startswith(key)
                    ]

        # Then create the query using like queries in the groups.
        if sections := data["cpc_section"]:
            cpc_query &= Q(
                cpc_groups__cpc_group__group__iregex=f"^({'|'.join(sections)})"
            )
        if classes := data["cpc_class"]:
            cpc_query &= Q(
                cpc_groups__cpc_group__group__iregex=f"^({'|'.join(classes)})"
            )
        if subclasses := data["cpc_subclass"]:
            cpc_query &= Q(
                cpc_groups__cpc_group__group__iregex=f"^({'|'.join(subclasses)})"
            )
        if groups := data["cpc_group"]:
            cpc_query &= Q(cpc_groups__cpc_group__in=groups)

        pct_query = range_query(
            "pct_data__published_or_filed_date", data["pct_application_date"]
        )
        if data["pct_granted"] is not None:
            pct_query &= Q(pct_data__granted=data["pct_granted"])

        inventor_query = Q()
        if data["inventor_first_name"]:
            inventor_query &= Q(
                inventors__first_name__iregex=f"^({'|'.join(data['inventor_first_name'])})"
            )
        if data["inventor_last_name"]:
            inventor_query &= Q(inventors__last_name__in=data["inventor_last_name"])

        if location := data["inventor_location"]:
            inventor_query &= Q(
                inventors__location__point__distance_lte=(
                    Point(location["lng"], location["lat"]),
                    D(m=location["radius"]),
                )
            )

        assignee_query = Q()
        if data["assignee_first_name"]:
            assignee_query &= Q(
                assignees__first_name__iregex=f"^({'|'.join(data['assignee_first_name'])})"
            )
        if data["assignee_last_name"]:
            assignee_query &= Q(assignees__last_name__in=data["assignee_last_name"])
        if data["assignee_organization"]:
            assignee_query &= Q(
                assignees__organization__in=data["assignee_organization"]
            )
        if location := data["assignee_location"]:
            assignee_query &= Q(
                assignees__location__point__distance_lte=(
                    Point(location["lng"], location["lat"]),
                    D(m=location["radius"]),
                )
            )

        query = patent_query & cpc_query & pct_query & inventor_query & assignee_query

        return Patent.objects.filter(query)

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
    def applications_per_year(patents: models.QuerySet) -> list:
        return list(
            patents.values("application_year")
            .annotate(count=Count("id"))
            .order_by("application_year")
            .values("application_year", "count")
        )

    @staticmethod
    def granted_patents_per_year(patents: models.QuerySet) -> list:
        return list(
            patents.values("granted_year")
            .annotate(count=Count("id"))
            .order_by("granted_year")
            .values("granted_year", "count")
        )

    @staticmethod
    def granted_patents_per_type_year(patents: models.QuerySet) -> list:
        return list(
            patents.values("granted_year", "type")
            .annotate(count=Count("id"))
            .order_by("granted_year", "type")
            .values("granted_year", "type", "count")
        )

    @staticmethod
    def granted_patents_per_office_year(patents: models.QuerySet) -> list:
        return list(
            patents.values("granted_year", "office")
            .annotate(count=Count("id"))
            .order_by("granted_year", "office")
            .values("granted_year", "office", "count")
        )

    @staticmethod
    def pct_protected_patents_per_year(patents: models.QuerySet) -> list:
        return list(
            patents.filter(pct_data__granted=True)
            .values("granted_year")
            .annotate(count=Count("id"))
            .order_by("granted_year")
            .values("granted_year", "count")
        )

    @staticmethod
    def granted_patents_per_cpc_year(patents: models.QuerySet) -> list:
        return list(
            patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
            .values("granted_year", "cpc_section")
            .annotate(count=Count("id"))
            .order_by("granted_year", "cpc_section")
            .values("granted_year", "cpc_section", "count")
        )

    @staticmethod
    def citations_made_per_year(patent_ids: list) -> list:
        return list(
            PatentCitation.objects.filter(citing_patent_id__in=patent_ids)
            .values("citation_year")
            .annotate(count=Count("citing_patent_id"))
            .order_by("citation_year")
            .values("citation_year", "count")
        )

    @staticmethod
    def citations_received_per_year(patent_ids: list) -> list:
        return list(
            PatentCitation.objects.filter(cited_patent_id__in=patent_ids)
            .values("citation_year")
            .annotate(count=Count("cited_patent_id"))
            .order_by("citation_year")
            .values("citation_year", "count")
        )

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
    def types(patents: models.QuerySet) -> list:
        return list(patents.values("type").annotate(count=Count("id")).order_by())

    @staticmethod
    def offices(patents: models.QuerySet) -> list:
        return list(patents.values("office").annotate(count=Count("id")).order_by())

    @staticmethod
    def top_10_inventors(patents: models.QuerySet) -> list:
        return list(
            patents.annotate(
                inventor=Concat(
                    "inventors__first_name", Value(" "), "inventors__last_name"
                )
            )
            .filter(~Q(inventor__iregex=r"^\s*$"))
            .values("inventor")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

    @staticmethod
    def inventor_locations(patents: models.QuerySet) -> list[dict]:
        return list(
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
            .values("lat", "lng", "location", "count")
        )

    @staticmethod
    def top_10_assignees(patents: models.QuerySet) -> list:
        return list(
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
        )

    @staticmethod
    def corporation_assignees_count(patents: models.QuerySet) -> int:
        return patents.filter(assignees__is_organization=True).count()

    @staticmethod
    def individual_assignees_count(patents: models.QuerySet) -> int:
        return patents.filter(assignees__is_organization=False).count()

    @staticmethod
    def assignee_locations(patents: models.QuerySet) -> list[dict]:
        return list(
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
            .values("lat", "lng", "location", "count")
        )

    @staticmethod
    def cpc_sections(patents: models.QuerySet) -> list:
        return list(
            patents.annotate(cpc_section=Substr("cpc_groups__cpc_group", 1, 1))
            .values("cpc_section")
            .annotate(count=Count("id"))
            .order_by("-count"),
        )

    @staticmethod
    def top_5_cpc_classes(patents: models.QuerySet) -> list:
        return list(
            patents.annotate(cpc_class=Substr("cpc_groups__cpc_group", 1, 3))
            .filter(~Q(cpc_class=""))
            .values("cpc_class")
            .annotate(count=Count("id"))
            .order_by("-count")[:5],
        )

    @staticmethod
    def top_5_cpc_subclasses(patents: models.QuerySet) -> list:
        return list(
            patents.annotate(cpc_subclass=Substr("cpc_groups__cpc_group", 1, 4))
            .filter(~Q(cpc_subclass=""))
            .values("cpc_subclass")
            .annotate(count=Count("id"))
            .order_by("-count")[:5],
        )

    @staticmethod
    def top_5_cpc_groups(patents: models.QuerySet) -> list:
        return list(
            patents.filter(cpc_groups__cpc_group__isnull=False)
            .values("cpc_groups__cpc_group")
            .annotate(count=Count("id"))
            .order_by("-count")[:5],
        )


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
        max_length=100, help_text="The ID of the patent in the PCT database."
    )
    published_or_filed_date = models.DateField(
        help_text="The date when the patent was published or filed by the office."
    )
    filed_country = models.CharField(
        max_length=100,
        help_text="The country code where the patent was filed in the PCT database.",
    )
    granted = models.BooleanField(
        help_text="Whether the patent is published and granted or it's just filed."
    )
    # Precomputed fields for optimization.
    representation = models.CharField(
        null=True, max_length=300, help_text="The representation of the PCT data."
    )
    objects = CopyManager()


class Location(models.Model):
    country_code = models.CharField(
        null=True, max_length=100, help_text="The country of the location."
    )
    state = models.CharField(
        null=True, max_length=100, help_text="The state of the location."
    )
    city = models.CharField(
        null=True, max_length=100, help_text="The city of the location."
    )
    point = models.PointField(
        null=True, help_text="The point (lat and lon) of the location."
    )
    county_fips = models.IntegerField(
        null=True, help_text="The FIPS code of the county."
    )
    state_fips = models.IntegerField(null=True, help_text="The FIPS code of the state.")

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
        help_text="The first name of the inventor.",
    )
    last_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="The last name of the inventor.",
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
        help_text="The first name of the assignee if the assignee is an individual.",
    )
    last_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="The last name of the assignee if the assignee is an individual.",
    )
    organization = models.CharField(
        null=True,
        max_length=100,
        help_text="The organization name if the assignee is an organization.",
    )
    # Precomputed fields for optimization.
    is_organization = models.BooleanField(
        null=True,
        default=None,
        help_text="Whether the assignee is an organization or an individual.",
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
        null=True, help_text="The date when the patent was cited."
    )
    cited_patent_number = models.CharField(
        null=True,
        max_length=100,
        help_text="The application number of the cited patent if it's not in the database.",
    )
    cited_patent_office = models.CharField(
        null=True,
        max_length=100,
        help_text="The country code of the cited patent if it's not in the database.",
    )
    # Precomputed fields for optimization.
    citation_year = models.IntegerField(
        null=True, default=None, help_text="The year when the patent was cited."
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
    def most_cited_patents_local(local_network_ids: list) -> list:
        return list(
            PatentCitation.objects.filter(id__in=local_network_ids)
            .values("cited_patent_id")
            .annotate(
                **PatentCitation.patent_annotation, count=Count("cited_patent_id")
            )
            .order_by("-count")[:10]
            .values("patent", "count")
        )

    @staticmethod
    def most_cited_patents_global(patent_ids: list) -> list:
        return list(
            PatentCitation.objects.filter(
                Q(citing_patent_id__in=patent_ids) | Q(cited_patent_id__in=patent_ids)
            )
            .values("cited_patent_id")
            .annotate(
                **PatentCitation.patent_annotation, count=Count("cited_patent_id")
            )
            .order_by("-count")[:10]
            .values("patent", "count")
        )
