from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization")
    search_fields = ("user__username", "organization__org_id")
    list_filter = ("organization",)
