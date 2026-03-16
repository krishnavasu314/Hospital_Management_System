from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)
    google_credentials = models.JSONField(default=dict, blank=True)
    google_calendar_email = models.EmailField(blank=True)
    google_calendar_connected_at = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ["email", "role"]

    @property
    def is_doctor(self) -> bool:
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self) -> bool:
        return self.role == self.Role.PATIENT

    @property
    def display_name(self) -> str:
        full_name = self.get_full_name().strip()
        return full_name or self.username

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_role_display()})"
