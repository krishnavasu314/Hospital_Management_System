# Mini Hospital Management System

Mini HMS is a Django web app for doctor availability management and patient appointment booking, backed by PostgreSQL for normal local use. It also includes a separate serverless email notification service built with the Serverless Framework and AWS Lambda conventions for local or cloud deployment.

## Features

- Role-based authentication for doctors and patients
- Login using username or email plus password
- Doctor dashboard for creating, editing, and deleting future availability slots
- Patient dashboard for filtering doctors and booking open future slots
- Transactional booking flow that locks the slot before creating the appointment
- Google Calendar sync hooks for both doctor and patient accounts
- Serverless email endpoint for signup and booking notifications

## Project Layout

- `config/`: Django project configuration
- `users/`: custom user model, auth routes, Google OAuth flow
- `appointments/`: availability slots, bookings, transactional booking service
- `templates/` and `static/`: server-rendered UI
- `serverless_email_service/`: standalone email notification Lambda project

## Local Setup

1. Create and activate a virtual environment.
2. Install Python dependencies with `py -m pip install -r requirements.txt`.
3. Copy `.env.example` values into your shell environment or a local `.env` loader of your choice.
4. Create a PostgreSQL database and update `DB_*` values.
5. Run `python manage.py migrate`.
6. Create an admin user with `python manage.py createsuperuser`.
7. Start Django with `python manage.py runserver`.

If `DB_NAME` is not set, the app falls back to SQLite so the codebase can still boot for quick checks.

## Google Calendar Setup

1. Create a Google Cloud project and enable the Google Calendar API.
2. Configure an OAuth client for a web application.
3. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID`, and `GOOGLE_OAUTH_REDIRECT_URI`.
4. In the app, sign in and use the `Connect Google` button from the navbar.

When a booking is confirmed, the app attempts to insert an event into the connected Google Calendar for both participants. If one side has not connected Google yet, the booking still succeeds and that calendar sync is skipped.

## Serverless Email Service

1. Move into `serverless_email_service/`.
2. Install Node dependencies with `npm install`.
3. Export the values from `serverless_email_service/.env.example`.
4. Run `npm run offline`.
5. Set Django `EMAIL_SERVICE_URL=http://127.0.0.1:3001/dev/notify`.

The Django app sends these actions:

- `SIGNUP_WELCOME`
- `BOOKING_CONFIRMATION`

## Demo Flow

For the 10-minute screen recording, use this order:

1. Show the Django project structure and the separate serverless email service.
2. Run the email service with `npm run offline`.
3. Run Django and sign up one doctor and one patient.
4. Connect Google Calendar for both accounts if credentials are configured.
5. Log in as the doctor and create future availability slots.
6. Log in as the patient, filter slots, and book one appointment.
7. Return to the doctor account and show that open slots can be edited or deleted, while booked slots are locked.
8. Show the booking blocked from a second patient account.
9. Show the confirmation records in the dashboard, admin, logs, or email inbox.
