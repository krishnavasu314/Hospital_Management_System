import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import AvailabilitySlot, Booking
from users.services import send_email_action


logger = logging.getLogger(__name__)


def build_event_payload(booking: Booking, counterparty_label: str) -> dict:
    return {
        "summary": f"Appointment with {counterparty_label}",
        "description": f"Hospital appointment between {booking.doctor.display_name} and {booking.patient.display_name}.",
        "start": {"dateTime": booking.slot.start_at.isoformat()},
        "end": {"dateTime": booking.slot.end_at.isoformat()},
    }


def _credentials_for_user(user):
    if not user.google_credentials:
        return None
    creds = Credentials.from_authorized_user_info(user.google_credentials, scopes=settings.GOOGLE_CALENDAR_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        user.google_credentials = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        user.save(update_fields=["google_credentials"])
    return creds


def create_calendar_events(booking: Booking) -> None:
    participants = [
        (booking.doctor, booking.patient.display_name, "doctor_calendar_event_id"),
        (booking.patient, f"Dr. {booking.doctor.display_name}", "patient_calendar_event_id"),
    ]

    for user, counterparty_label, booking_field in participants:
        try:
            credentials = _credentials_for_user(user)
            if not credentials:
                continue
            service = build("calendar", "v3", credentials=credentials)
            event = build_event_payload(booking, counterparty_label)
            created_event = service.events().insert(calendarId="primary", body=event).execute()
            setattr(booking, booking_field, created_event.get("id", ""))
        except Exception:
            logger.exception("Failed to create Google Calendar event for user_id=%s", user.pk)

    booking.save(update_fields=["doctor_calendar_event_id", "patient_calendar_event_id"])


def send_booking_confirmation(booking: Booking) -> None:
    booking_payload = {
        "doctor_name": booking.doctor.display_name,
        "patient_name": booking.patient.display_name,
        "start_at": booking.slot.start_at.isoformat(),
        "end_at": booking.slot.end_at.isoformat(),
    }
    send_email_action("BOOKING_CONFIRMATION", booking.patient.email, booking_payload)
    send_email_action("BOOKING_CONFIRMATION", booking.doctor.email, booking_payload)


def finalize_booking(booking_id: int) -> None:
    booking = Booking.objects.select_related("doctor", "patient", "slot").get(pk=booking_id)
    create_calendar_events(booking)
    send_booking_confirmation(booking)


def book_slot_for_patient(slot_id: int, patient) -> Booking:
    with transaction.atomic():
        slot = (
            AvailabilitySlot.objects.select_for_update()
            .select_related("doctor")
            .get(pk=slot_id)
        )

        if slot.start_at <= timezone.now():
            raise ValidationError("This slot is no longer in the future.")

        if hasattr(slot, "booking"):
            raise ValidationError("This slot has already been booked.")

        booking = Booking.objects.create(
            slot=slot,
            doctor=slot.doctor,
            patient=patient,
        )
        transaction.on_commit(lambda: finalize_booking(booking.pk))
        return booking
