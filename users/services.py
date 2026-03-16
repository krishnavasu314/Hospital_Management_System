import logging

from django.conf import settings
from django.utils import timezone

import requests
from google_auth_oauthlib.flow import Flow


logger = logging.getLogger(__name__)


def send_email_action(action: str, recipient_email: str, payload: dict) -> None:
    if not settings.EMAIL_SERVICE_URL:
        return

    headers = {"Content-Type": "application/json"}
    if settings.EMAIL_SERVICE_API_KEY:
        headers["x-api-key"] = settings.EMAIL_SERVICE_API_KEY

    body = {
        "action": action,
        "recipient_email": recipient_email,
        "payload": payload,
    }

    try:
        requests.post(
            settings.EMAIL_SERVICE_URL,
            json=body,
            headers=headers,
            timeout=settings.EMAIL_SERVICE_TIMEOUT,
        ).raise_for_status()
    except requests.RequestException:
        logger.exception("Email notification request failed for action=%s", action)


def send_signup_welcome_email(user) -> None:
    send_email_action(
        action="SIGNUP_WELCOME",
        recipient_email=user.email,
        payload={
            "name": user.display_name,
            "role": user.get_role_display(),
        },
    )


def google_oauth_available() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_OAUTH_REDIRECT_URI)


def build_google_flow(state: str | None = None, code_verifier: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        settings.GOOGLE_OAUTH_CONFIG,
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    if code_verifier:
        flow.code_verifier = code_verifier
    return flow


def persist_google_credentials(user, credentials) -> None:
    credential_payload = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    user.google_credentials = credential_payload
    user.google_calendar_connected_at = timezone.now()
    user.save(update_fields=["google_credentials", "google_calendar_connected_at"])
