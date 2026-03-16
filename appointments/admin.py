from django.contrib import admin

from .models import AvailabilitySlot, Booking


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("doctor", "start_at", "end_at", "created_at")
    list_filter = ("doctor",)
    search_fields = ("doctor__username", "doctor__email")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("doctor", "patient", "slot", "created_at")
    list_filter = ("doctor", "patient")
    search_fields = ("doctor__username", "patient__username", "doctor__email", "patient__email")
