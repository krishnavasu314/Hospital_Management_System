from django.urls import path

from .views import book_slot, delete_availability, doctor_dashboard, edit_availability, patient_dashboard


urlpatterns = [
    path("doctor/dashboard/", doctor_dashboard, name="doctor-dashboard"),
    path("doctor/availability/<int:slot_id>/edit/", edit_availability, name="edit-availability"),
    path("doctor/availability/<int:slot_id>/delete/", delete_availability, name="delete-availability"),
    path("patient/dashboard/", patient_dashboard, name="patient-dashboard"),
    path("patient/book/<int:slot_id>/", book_slot, name="book-slot"),
]
