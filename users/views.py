import secrets

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from googleapiclient.discovery import build

from .forms import SignUpForm, StyledAuthenticationForm
from .services import (
    build_google_flow,
    google_oauth_available,
    persist_google_credentials,
    send_signup_welcome_email,
)


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = StyledAuthenticationForm


class UserLogoutView(LogoutView):
    pass


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_signup_welcome_email(user)
            messages.success(request, "Account created. You can start using your dashboard now.")
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "users/signup.html", {"form": form})


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    if request.user.is_doctor:
        return redirect("doctor-dashboard")
    return redirect("patient-dashboard")


@login_required
def google_connect(request: HttpRequest) -> HttpResponse:
    if not google_oauth_available():
        messages.error(request, "Google OAuth is not configured in the environment.")
        return redirect("dashboard")

    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state
    flow = build_google_flow(state=state)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge_method="S256",
    )
    if getattr(flow, "code_verifier", None):
        request.session["google_oauth_code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@login_required
def google_callback(request: HttpRequest) -> HttpResponse:
    if request.GET.get("error"):
        messages.error(request, f"Google OAuth was not completed: {request.GET['error']}.")
        return redirect("dashboard")

    expected_state = request.session.get("google_oauth_state")
    expected_code_verifier = request.session.get("google_oauth_code_verifier")
    state = request.GET.get("state")
    if not expected_state or state != expected_state:
        messages.error(request, "Google OAuth state validation failed.")
        return redirect("dashboard")

    flow = build_google_flow(state=state, code_verifier=expected_code_verifier)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    persist_google_credentials(request.user, credentials)

    if credentials.id_token:
        try:
            user_info = id_token.verify_oauth2_token(credentials.id_token, GoogleRequest(), audience=credentials.client_id)
            request.user.google_calendar_email = user_info.get("email", "")
            request.user.save(update_fields=["google_calendar_email"])
        except Exception:
            pass
    else:
        try:
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            request.user.google_calendar_email = user_info.get("email", "")
            request.user.save(update_fields=["google_calendar_email"])
        except Exception:
            pass

    request.session.pop("google_oauth_state", None)
    request.session.pop("google_oauth_code_verifier", None)
    messages.success(request, "Google Calendar connected successfully.")
    return redirect("dashboard")
