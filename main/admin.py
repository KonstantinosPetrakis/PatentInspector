from leaflet.admin import LeafletGeoAdmin
from django.contrib import admin
from django.contrib.auth.models import Group, User
from main.models import *


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


# Location
admin.site.register(Location, LocationAdmin)
# CPC Fields
admin.site.register(CPCSection, CPCSectionAdmin)
admin.site.register(CPCClass, CPCClassAdmin)
admin.site.register(CPCSubclass, CPCSubclassAdmin)
admin.site.register(CPCGroup, CPCGroupAdmin)
# Unregister Auth related fields
admin.site.unregister(User)
admin.site.unregister(Group)