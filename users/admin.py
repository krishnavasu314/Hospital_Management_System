from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "HMS",
            {
                "fields": (
                    "role",
                    "google_credentials",
                    "google_calendar_email",
                    "google_calendar_connected_at",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "HMS",
            {
                "classes": ("wide",),
                "fields": ("email", "role"),
            },
        ),
    )
    list_display = ("username", "email", "role", "is_staff")
