from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AvailabilitySlotForm, SlotFilterForm
from .models import AvailabilitySlot, Booking
from .services import book_slot_for_patient
from users.models import CustomUser


def _get_doctor_slot_or_404(user, slot_id: int) -> AvailabilitySlot:
    return get_object_or_404(AvailabilitySlot.objects.select_related("doctor"), pk=slot_id, doctor=user)


@login_required
def doctor_dashboard(request: HttpRequest) -> HttpResponse:
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can access the doctor dashboard.")
        return redirect("patient-dashboard")

    if request.method == "POST":
        form = AvailabilitySlotForm(request.POST, doctor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Availability slot created.")
            return redirect("doctor-dashboard")
    else:
        form = AvailabilitySlotForm(doctor=request.user)

    slots = request.user.availability_slots.all().prefetch_related("booking__patient")
    bookings = Booking.objects.filter(doctor=request.user).select_related("patient", "slot")
    return render(
        request,
        "appointments/doctor_dashboard.html",
        {
            "slot_form": form,
            "slots": slots,
            "bookings": bookings,
        },
    )


@login_required
def edit_availability(request: HttpRequest, slot_id: int) -> HttpResponse:
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can edit availability.")
        return redirect("dashboard")

    slot = _get_doctor_slot_or_404(request.user, slot_id)
    if hasattr(slot, "booking"):
        messages.error(request, "Booked slots cannot be edited.")
        return redirect("doctor-dashboard")

    if request.method == "POST":
        form = AvailabilitySlotForm(request.POST, doctor=request.user, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "Availability slot updated.")
            return redirect("doctor-dashboard")
    else:
        form = AvailabilitySlotForm(doctor=request.user, instance=slot)

    return render(
        request,
        "appointments/edit_availability.html",
        {
            "slot": slot,
            "slot_form": form,
        },
    )


@login_required
def delete_availability(request: HttpRequest, slot_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("doctor-dashboard")

    if not request.user.is_doctor:
        messages.error(request, "Only doctors can delete availability.")
        return redirect("dashboard")

    slot = _get_doctor_slot_or_404(request.user, slot_id)
    if hasattr(slot, "booking"):
        messages.error(request, "Booked slots cannot be deleted.")
        return redirect("doctor-dashboard")

    slot.delete()
    messages.success(request, "Availability slot deleted.")
    return redirect("doctor-dashboard")


@login_required
def patient_dashboard(request: HttpRequest) -> HttpResponse:
    if not request.user.is_patient:
        messages.error(request, "Only patients can access the patient dashboard.")
        return redirect("doctor-dashboard")

    filter_form = SlotFilterForm(request.GET or None)
    slots = AvailabilitySlot.objects.available().select_related("doctor")
    if filter_form.is_valid():
        doctor = filter_form.cleaned_data.get("doctor")
        date = filter_form.cleaned_data.get("date")
        if doctor:
            slots = slots.filter(doctor=doctor)
        if date:
            slots = slots.filter(start_at__date=date)

    doctors = CustomUser.objects.filter(role=CustomUser.Role.DOCTOR).order_by("first_name", "username")
    bookings = Booking.objects.filter(patient=request.user).select_related("doctor", "slot")
    return render(
        request,
        "appointments/patient_dashboard.html",
        {
            "doctors": doctors,
            "available_slots": slots,
            "bookings": bookings,
            "filter_form": filter_form,
        },
    )


@login_required
def book_slot(request: HttpRequest, slot_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("patient-dashboard")

    if not request.user.is_patient:
        messages.error(request, "Only patients can book appointments.")
        return redirect("dashboard")

    slot = get_object_or_404(AvailabilitySlot, pk=slot_id)
    try:
        book_slot_for_patient(slot.pk, request.user)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, f"Appointment booked with Dr. {slot.doctor.display_name}.")
    return redirect("patient-dashboard")
