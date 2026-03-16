from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("username", "first_name", "last_name", "email"):
            self.fields[field_name].widget.attrs.update({"class": "form-input"})
        self.fields["role"].widget.attrs.update({"class": "form-input"})
        self.fields["password1"].widget.attrs.update({"class": "form-input"})
        self.fields["password2"].widget.attrs.update({"class": "form-input"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-input"})
        self.fields["password"].widget.attrs.update({"class": "form-input"})

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
