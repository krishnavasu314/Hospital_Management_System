from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import AvailabilitySlot, Booking
from appointments.services import book_slot_for_patient
from users.models import CustomUser


class BookingServiceTests(TestCase):
    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.DOCTOR,
        )
        self.patient = CustomUser.objects.create_user(
            username="patient",
            email="patient@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.PATIENT,
        )
        self.other_patient = CustomUser.objects.create_user(
            username="patient2",
            email="patient2@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.PATIENT,
        )
        self.slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, minutes=30),
        )

    def test_books_open_slot(self):
        with self.captureOnCommitCallbacks(execute=True):
            booking = book_slot_for_patient(self.slot.pk, self.patient)

        self.assertEqual(booking.patient, self.patient)
        self.assertTrue(Booking.objects.filter(slot=self.slot).exists())

    def test_prevents_double_booking(self):
        with self.captureOnCommitCallbacks(execute=True):
            book_slot_for_patient(self.slot.pk, self.patient)

        with self.assertRaises(ValidationError):
            book_slot_for_patient(self.slot.pk, self.other_patient)


class DoctorAvailabilityManagementTests(TestCase):
    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username="doctor-manage",
            email="doctor-manage@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.DOCTOR,
        )
        self.other_doctor = CustomUser.objects.create_user(
            username="other-doctor",
            email="other-doctor@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.DOCTOR,
        )
        self.patient = CustomUser.objects.create_user(
            username="patient-manage",
            email="patient-manage@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.PATIENT,
        )
        self.slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            start_at=timezone.now() + timedelta(days=2),
            end_at=timezone.now() + timedelta(days=2, minutes=30),
        )

    def test_doctor_can_edit_own_unbooked_slot(self):
        self.client.force_login(self.doctor)
        response = self.client.post(
            reverse("edit-availability", args=[self.slot.pk]),
            {
                "date": (timezone.localtime(self.slot.start_at) + timedelta(days=1)).date().isoformat(),
                "start_time": "10:00",
                "end_time": "10:30",
            },
        )

        self.assertRedirects(response, reverse("doctor-dashboard"))
        self.slot.refresh_from_db()
        self.assertEqual(timezone.localtime(self.slot.start_at).hour, 10)
        self.assertEqual(timezone.localtime(self.slot.end_at).hour, 10)
        self.assertEqual(timezone.localtime(self.slot.end_at).minute, 30)

    def test_doctor_cannot_edit_other_doctor_slot(self):
        self.client.force_login(self.other_doctor)
        response = self.client.get(reverse("edit-availability", args=[self.slot.pk]))

        self.assertEqual(response.status_code, 404)

    def test_booked_slot_cannot_be_deleted(self):
        Booking.objects.create(
            slot=self.slot,
            doctor=self.doctor,
            patient=self.patient,
        )
        self.client.force_login(self.doctor)
        response = self.client.post(reverse("delete-availability", args=[self.slot.pk]))

        self.assertRedirects(response, reverse("doctor-dashboard"))
        self.assertTrue(AvailabilitySlot.objects.filter(pk=self.slot.pk).exists())
