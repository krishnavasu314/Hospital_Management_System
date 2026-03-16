from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import AvailabilitySlot


User = get_user_model()


class AvailabilitySlotForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-input"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time", "class": "form-input"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time", "class": "form-input"}))

    def __init__(self, *args, doctor=None, instance=None, **kwargs):
        self.doctor = doctor
        self.instance = instance
        super().__init__(*args, **kwargs)
        if self.instance and not self.is_bound:
            local_start = timezone.localtime(self.instance.start_at)
            local_end = timezone.localtime(self.instance.end_at)
            self.initial.update(
                {
                    "date": local_start.date(),
                    "start_time": local_start.time().replace(second=0, microsecond=0),
                    "end_time": local_end.time().replace(second=0, microsecond=0),
                }
            )

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if not all([date, start_time, end_time, self.doctor]):
            return cleaned_data

        start_at = timezone.make_aware(datetime.combine(date, start_time))
        end_at = timezone.make_aware(datetime.combine(date, end_time))

        if end_at <= start_at:
            raise forms.ValidationError("End time must be after start time.")

        if start_at <= timezone.now():
            raise forms.ValidationError("Availability must be created in the future.")

        overlaps = AvailabilitySlot.objects.filter(
            doctor=self.doctor,
            start_at__lt=end_at,
            end_at__gt=start_at,
        )
        if self.instance:
            overlaps = overlaps.exclude(pk=self.instance.pk)
        if overlaps.exists():
            raise forms.ValidationError("This slot overlaps with an existing availability window.")

        cleaned_data["start_at"] = start_at
        cleaned_data["end_at"] = end_at
        return cleaned_data

    def save(self):
        if self.instance:
            self.instance.start_at = self.cleaned_data["start_at"]
            self.instance.end_at = self.cleaned_data["end_at"]
            self.instance.save(update_fields=["start_at", "end_at"])
            return self.instance

        return AvailabilitySlot.objects.create(
            doctor=self.doctor,
            start_at=self.cleaned_data["start_at"],
            end_at=self.cleaned_data["end_at"],
        )


class SlotFilterForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="All doctors",
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = User.objects.filter(role=User.Role.DOCTOR).order_by("first_name", "username")
