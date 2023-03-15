from django.core.paginator import Paginator
from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin
from django.contrib.auth.models import Group, User
from main.models import *


class PatentCPCGroupInline(admin.TabularInline):
    model = PatentCPCGroup
    autocomplete_fields = ("cpc_group", )
    extra = 0


class PatentAdmin(admin.ModelAdmin):
    list_display = ("id", "office", "office_patent_id", "title", "type")
    list_filter = ("type", "office")
    search_fields = ("title", "abstract", "office")
    inlines = [PatentCPCGroupInline]


class LocationAdmin(LeafletGeoAdmin):
    list_display = ("country_code", "city")
    list_filter = ("country_code", )
    search_fields = ("city", "country_code", "state", "county_fips", "state_fips")


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
admin.site.register(Location, LocationAdmin)

# CPC related
admin.site.register(CPCSection, CPCSectionAdmin)
admin.site.register(CPCClass, CPCClassAdmin)
admin.site.register(CPCSubclass, CPCSubclassAdmin)
admin.site.register(CPCGroup, CPCGroupAdmin)

# Unregister Auth related fields
admin.site.unregister(User)
admin.site.unregister(Group)