from django.db.models.query import QuerySet
from django.contrib import admin
from django.contrib.auth.models import Group, User
from leaflet.admin import LeafletGeoAdmin

from main.models import *


class FastCountAdmin(admin.ModelAdmin):
    class FastCountQuerySet(QuerySet):
        def count(self):
            """
            Override count queries (performed by Django ORM) to display approximate value.
            This will speed up count in the admin interface.
            """

            if self._result_cache is not None:
                return len(self._result_cache)

            query = self.query
            if not (query.group_by or query.where or query.distinct):
                cursor = connection.cursor()
                cursor.execute("SELECT reltuples FROM pg_class WHERE relname = %s", 
                    [self.model._meta.db_table])
                return int(cursor.fetchone()[0])
            else:
                return self.query.get_count(using=self.db)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return FastCountAdmin.FastCountQuerySet(qs.model, using=qs.db)


# Patent related definitions
class PatentCPCGroupInline(admin.TabularInline):
    model = PatentCPCGroup
    autocomplete_fields = ("cpc_group", )
    extra = 0


class PatentPCTDataInline(admin.TabularInline):
    model = PCTData
    extra = 0


class PatentCitedByInline(admin.TabularInline):
    verbose_name = "Cited by"
    verbose_name_plural = "Cited by"
    fk_name = "cited_patent"
    model = PatentCitation
    autocomplete_fields = ("cited_patent", "citing_patent")
    extra = 0
    classes = ['collapse']


class PatentCitesInline(admin.TabularInline):
    verbose_name = "Citation"
    verbose_name_plural = "Citations"
    fk_name = "citing_patent"
    model = PatentCitation
    autocomplete_fields = ("cited_patent", "citing_patent")
    extra = 0
    classes = ['collapse']


class InventorInline(admin.TabularInline):
    model = Inventor
    autocomplete_fields = ("location", )
    extra = 0


class AssigneeInline(admin.TabularInline):
    model = Assignee
    autocomplete_fields = ("location", )
    extra = 0


class PatentAdmin(FastCountAdmin):
    class HasPCTApplicationFilter(admin.SimpleListFilter):
        title = "existence of a PCT application"
        parameter_name = "has_pct_application"

        def lookups(self, request, model_admin):
            return (("yes", "Yes"), ("no", "No"))

        def queryset(self, request, queryset):
            if self.value() == "yes":
                return queryset.exclude(pct_data__isnull=True)
            elif self.value() == "no":
                return queryset.filter(pct_data__isnull=True)
            return queryset

    list_display = ("id", "office", "office_patent_id", "title", "type")
    list_filter = ("type", "office", HasPCTApplicationFilter)
    search_fields = ("title", "abstract", "office", "office_patent_id")
    inlines = [InventorInline, AssigneeInline, PatentCPCGroupInline, PatentPCTDataInline, PatentCitedByInline, PatentCitesInline,]


class PatentCitationAdmin(FastCountAdmin):
    model = PatentCitation
    list_display = ("id", "citation_date", "cited_patent_number")
    search_fields = ("cited_patent_number", )
    autocomplete_fields = ("citing_patent", "cited_patent")


class LocationAdmin(LeafletGeoAdmin):
    list_display = ("country_code", "city")
    list_filter = ("country_code", )
    search_fields = ("city", "country_code", "state", "county_fips", "state_fips")


class InventorAdmin(FastCountAdmin):
    list_filter = ("male", )
    search_fields = ("last_name", "first_name", )
    ordering = ("last_name", "first_name")
    autocomplete_fields = ("patent", "location")


class AssigneeAdmin(FastCountAdmin):
    class IsOrganizationFilter(admin.SimpleListFilter):
        title = "whether the assignee is an organization"
        parameter_name = "organization"

        def lookups(self, request, model_admin):
            return (("yes", "Yes"), ("no", "No"))
        
        def queryset(self, request, queryset):
            if self.value() == "no":
                return queryset.filter(organization__isnull=True)
            elif self.value() == "yes":
                return queryset.exclude(organization__isnull=True)
            return queryset

    search_fields = ("organization", "last_name", "first_name")
    ordering = ("organization", "last_name", "first_name")
    autocomplete_fields = ("patent", "location")
    list_filter = [IsOrganizationFilter]


# CPC related definitions
class CPCSectionAdmin(admin.ModelAdmin):
    list_display = ("section", "title")
    search_fields = ("section", "title")
    ordering = ("section", )


class CPCClassAdmin(admin.ModelAdmin):
    list_display = ("_class", "title")
    search_fields = ("_class", "title")
    ordering = ("_class", )


class CPCSubclassAdmin(admin.ModelAdmin):
    list_display = ("subclass", "title")
    search_fields = ("subclass", "title")
    ordering = ("subclass", )


class CPCGroupAdmin(admin.ModelAdmin):
    list_display = ("group", "title")
    search_fields = ("group", "title")
    ordering = ("group", )


# Patent related
admin.site.register(Patent, PatentAdmin)
admin.site.register(PatentCitation, PatentCitationAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Inventor, InventorAdmin)
admin.site.register(Assignee, AssigneeAdmin)

# CPC related
admin.site.register(CPCSection, CPCSectionAdmin)
admin.site.register(CPCClass, CPCClassAdmin)
admin.site.register(CPCSubclass, CPCSubclassAdmin)
admin.site.register(CPCGroup, CPCGroupAdmin)

# Unregister Auth related fields
admin.site.unregister(User)
admin.site.unregister(Group)

# Customize admin site
admin.site.site_header = "PatentAnalyzer Administration"
admin.site.site_title = "PatentAnalyzer Administration"
admin.site.index_title = "PatentAnalyzer Administration"
