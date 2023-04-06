from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin
from django.contrib.auth.models import Group, User
from main.models import *


# Patent related definitions
class PatentCPCGroupInline(admin.TabularInline):
    model = PatentCPCGroup
    autocomplete_fields = ("cpc_group", )
    extra = 0


class PatentPCTDataInline(admin.TabularInline):
    model = PCTData
    extra = 0


class PatentAdmin(admin.ModelAdmin):
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
    search_fields = ("search_vector", "office", "office_patent_id")
    inlines = [PatentCPCGroupInline, PatentPCTDataInline]


class PatentCitationAdmin(admin.ModelAdmin):
    model = PatentCitation
    list_display = ("id", "record_name", "citation_date", "cited_patent_number")
    search_fields = ("cited_patent_number", "record_name")
    autocomplete_fields = ("citing_patent", "cited_patent")


class LocationAdmin(LeafletGeoAdmin):
    list_display = ("country_code", "city")
    list_filter = ("country_code", )
    search_fields = ("city", "country_code", "state", "county_fips", "state_fips")


class InventorAdmin(admin.ModelAdmin):
    list_filter = ("male", )
    search_fields = ("last_name", "first_name", )
    ordering = ("last_name", "first_name")
    autocomplete_fields = ("patent", "location")


class AssigneeAdmin(admin.ModelAdmin):
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
