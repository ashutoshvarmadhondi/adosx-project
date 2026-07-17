from django.contrib import admin

from django.contrib import admin

from .models import Location, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("org_id", "name")
    search_fields = ("org_id", "name")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("location_id", "name", "organization")
    search_fields = ("location_id", "name", "organization__org_id")
    list_filter = ("organization",)
