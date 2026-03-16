import json
import os
import smtplib
from email.mime.text import MIMEText


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _parse_body(event: dict) -> dict:
    body = event.get("body", "{}")
    if isinstance(body, str):
        return json.loads(body or "{}")
    return body


def _authorize(event: dict) -> bool:
    configured_key = os.environ.get("EMAIL_SERVICE_API_KEY", "")
    if not configured_key:
        return True

    headers = event.get("headers") or {}
    incoming_key = headers.get("x-api-key") or headers.get("X-Api-Key")
    return incoming_key == configured_key


def _render_message(action: str, payload: dict) -> tuple[str, str]:
    if action == "SIGNUP_WELCOME":
        role = payload.get("role", "User")
        name = payload.get("name", "there")
        subject = "Welcome to Mini HMS"
        body = (
            f"Hello {name},\n\n"
            f"Welcome to Mini HMS. Your {role.lower()} account is ready.\n"
            "You can now log in, manage availability, or book appointments.\n\n"
            "Regards,\nMini HMS"
        )
        return subject, body

    if action == "BOOKING_CONFIRMATION":
        subject = "Appointment confirmation"
        body = (
            "Your appointment details are below.\n\n"
            f"Doctor: {payload.get('doctor_name', 'N/A')}\n"
            f"Patient: {payload.get('patient_name', 'N/A')}\n"
            f"Start: {payload.get('start_at', 'N/A')}\n"
            f"End: {payload.get('end_at', 'N/A')}\n\n"
            "Regards,\nMini HMS"
        )
        return subject, body

    raise ValueError("Unsupported action")


def _send_email(recipient_email: str, subject: str, body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    from_email = os.environ.get("SMTP_FROM_EMAIL", smtp_username)

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient_email

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, [recipient_email], message.as_string())


def handler(event, context):
    if not _authorize(event):
        return _response(401, {"ok": False, "error": "Unauthorized"})

    try:
        body = _parse_body(event)
    except json.JSONDecodeError:
        return _response(400, {"ok": False, "error": "Invalid JSON"})

    action = body.get("action")
    recipient_email = body.get("recipient_email")
    payload = body.get("payload") or {}

    if not action or not recipient_email:
        return _response(400, {"ok": False, "error": "action and recipient_email are required"})

    try:
        subject, message_body = _render_message(action, payload)
        _send_email(recipient_email, subject, message_body)
    except KeyError as exc:
        return _response(500, {"ok": False, "error": f"Missing SMTP configuration: {exc.args[0]}"})
    except ValueError as exc:
        return _response(400, {"ok": False, "error": str(exc)})
    except Exception as exc:
        return _response(500, {"ok": False, "error": str(exc)})

    return _response(200, {"ok": True, "action": action, "recipient_email": recipient_email})
