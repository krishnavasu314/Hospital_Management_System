from django.conf import settings
from django.db import models
from django.utils import timezone


class AvailabilitySlotQuerySet(models.QuerySet):
    def future(self):
        return self.filter(start_at__gt=timezone.now())

    def available(self):
        return self.future().filter(booking__isnull=True)


class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availability_slots",
        limit_choices_to={"role": "doctor"},
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AvailabilitySlotQuerySet.as_manager()

    class Meta:
        ordering = ("start_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("doctor", "start_at", "end_at"),
                name="unique_doctor_exact_slot",
            )
        ]

    def __str__(self) -> str:
        return f"{self.doctor.display_name}: {self.start_at} - {self.end_at}"


class Booking(models.Model):
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE, related_name="booking")
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_bookings",
        limit_choices_to={"role": "doctor"},
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_bookings",
        limit_choices_to={"role": "patient"},
    )
    notes = models.TextField(blank=True)
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True)
    patient_calendar_event_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("slot__start_at",)

    def __str__(self) -> str:
        return f"{self.patient.display_name} with {self.doctor.display_name} at {self.slot.start_at}"
