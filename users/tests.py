from django.test import TestCase
from django.urls import reverse

from .forms import SignUpForm
from .models import CustomUser


class SignUpFormTests(TestCase):
    def test_rejects_duplicate_email(self):
        CustomUser.objects.create_user(
            username="doctor1",
            email="doctor@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.DOCTOR,
        )
        form = SignUpForm(
            data={
                "username": "doctor2",
                "first_name": "New",
                "last_name": "Doctor",
                "email": "doctor@example.com",
                "role": CustomUser.Role.DOCTOR,
                "password1": "SafePassword123!",
                "password2": "SafePassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="doctor1",
            email="doctor@example.com",
            password="SafePassword123!",
            role=CustomUser.Role.DOCTOR,
        )

    def test_logs_in_with_email_address(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "doctor@example.com",
                "password": "SafePassword123!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("doctor-dashboard"))
