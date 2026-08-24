# Healthcare Appointment & Follow-up Manager

A backend healthcare appointment management system built with Flask and PostgreSQL. The system supports patient and doctor workflows including appointment booking, temporary slot holds, doctor working hours and leave management, symptom submission, AI-generated pre-visit summaries, notifications, reminders, consultations, prescriptions, and follow-ups.

---

## 1. Project Overview

The Healthcare Appointment & Follow-up Manager is designed to provide a structured workflow for managing doctor appointments and follow-up care.

The system supports three main user roles:

* **Patient**

  * Register and log in
  * View available doctors
  * View appointment availability
  * Temporarily hold an appointment slot
  * Confirm appointments
  * Cancel appointments
  * Submit symptoms before a visit
  * Receive an AI-generated pre-visit summary
  * View notifications and reminders

* **Doctor**

  * Log in securely
  * Configure/view working hours
  * Manage leave
  * View appointments
  * View patient symptoms
  * View AI-generated pre-visit summaries
  * Manage consultations, prescriptions, and follow-ups

* **Admin**

  * User/account management functionality can be extended through the backend structure.

---

# 2. Tech Stack

| Component            | Technology                    |
| -------------------- | ----------------------------- |
| Backend              | Flask                         |
| Programming Language | Python                        |
| Database             | PostgreSQL                    |
| ORM                  | Flask-SQLAlchemy / SQLAlchemy |
| Authentication       | JWT                           |
| Password Security    | Werkzeug password hashing     |
| AI / LLM             | Ollama                        |
| Local LLM            | Llama 3.2 3B                  |
| API Testing          | Postman                       |
| Version Control      | Git / GitHub                  |

---

# 3. Project Structure

```text
healthcare-appointment-manager/
│
├── backend/
│   ├── app.py
│   │
│   ├── config/
│   │   └── config.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── appointment.py
│   │   ├── working_hour.py
│   │   ├── doctor_leave.py
│   │   ├── slot_hold.py
│   │   ├── symptom.py
│   │   ├── ai_summary.py
│   │   ├── notification.py
│   │   ├── reminder.py
│   │   ├── consultation.py
│   │   ├── prescription.py
│   │   ├── medication.py
│   │   └── follow_up.py
│   │
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── appointment_routes.py
│   │   ├── availability_routes.py
│   │   ├── doctor_routes.py
│   │   ├── symptom_routes.py
│   │   ├── notification_routes.py
│   │   ├── reminder_routes.py
│   │   ├── consultation_routes.py
│   │   ├── prescription_routes.py
│   │   └── follow_up_routes.py
│   │
│   └── services/
│       ├── ai_summary_service.py
│       └── reminder_scheduler.py
│
├── database/
│   ├── __init__.py
│   └── database.py
│
├── create_index.py
├── create_slot_hold_table.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 4. Setup Guide

## Prerequisites

Install the following:

* Python 3.10+
* PostgreSQL
* Git
* Ollama
* Llama 3.2 3B model

Verify the installations:

```bash
python --version
psql --version
git --version
ollama --version
```

---

## Clone the repository

```bash
git clone https://github.com/WilhelminaSA/healthcare-appointment-manager.git
cd healthcare-appointment-manager
```

---

## Create a virtual environment

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

---

## Install dependencies

```powershell
pip install -r requirements.txt
```

---

# 5. Environment Variables

Create a `.env` file in the project root.

Use `.env.example` as the template:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

JWT_SECRET_KEY=change_this_to_a_random_secret

LLM_API_KEY=your_llm_api_key
```

Do **not** commit the `.env` file to GitHub.

The `.gitignore` file already excludes:

```text
.env
.venv/
__pycache__/
```

---

# 6. PostgreSQL Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE healthcare_db;
```

Configure the database credentials in `.env`.

The Flask application uses SQLAlchemy to communicate with PostgreSQL.

The database connection is configured through:

```text
backend/config/config.py
```

and:

```text
database/database.py
```

---

# 7. Database Schema

The project uses the following primary entities.

## users

Stores authentication and role information.

```text
users
├── id (PK)
├── name
├── email
├── password_hash
└── role
```

Supported roles include:

```text
patient
doctor
admin
```

---

## patients

Stores patient-specific information.

```text
patients
├── id (PK)
├── user_id (FK → users.id)
├── phone
└── address
```

---

## doctors

Stores doctor-specific information.

```text
doctors
├── id (PK)
├── user_id (FK → users.id)
├── specialization
├── license_number
└── phone
```

---

## appointments

Stores scheduled appointments.

```text
appointments
├── id (PK)
├── patient_id (FK → patients.id)
├── doctor_id (FK → doctors.id)
├── appointment_date
├── reason
└── status
```

Typical appointment statuses include:

```text
scheduled
cancelled
completed
```

---

## working_hours

Stores the doctor's available working schedule.

```text
working_hours
├── id (PK)
├── doctor_id (FK → doctors.id)
├── day_of_week
├── start_time
├── end_time
└── slot_duration
```

The `slot_duration` determines the valid appointment intervals.

---

## doctor_leaves

Stores dates on which a doctor is unavailable.

```text
doctor_leaves
├── id (PK)
├── doctor_id (FK → doctors.id)
└── leave_date
```

Appointments cannot be booked when the doctor is on leave.

---

## slot_holds

Temporarily reserves an appointment slot before final confirmation.

```text
slot_holds
├── id (PK)
├── doctor_id (FK → doctors.id)
├── patient_id (FK → patients.id)
├── appointment_date
└── expires_at
```

A slot hold expires after the configured hold period.

The implementation also uses database-level uniqueness to protect against concurrent slot holds.

---

## symptoms

Stores symptoms submitted by the patient before an appointment.

```text
symptoms
├── id (PK)
├── appointment_id (FK → appointments.id)
├── description
└── created_at
```

---

## ai_summaries

Stores the AI-generated pre-visit summary.

```text
ai_summaries
├── id (PK)
├── appointment_id (FK → appointments.id)
├── urgency_level
├── chief_complaint
├── suggested_question_1
├── suggested_question_2
└── suggested_question_3
```

The AI summary is associated with the appointment rather than being stored only as temporary output.

---

## notifications

Stores application notifications.

```text
notifications
├── id (PK)
├── user_id (FK → users.id)
├── notification_type
├── message
└── sent
```

Notifications are created for important appointment events such as booking and cancellation.

---

## reminders

Stores reminder information related to appointments.

```text
reminders
├── id (PK)
├── appointment_id (FK → appointments.id)
├── reminder_time
└── sent
```

---

## consultations

Stores consultation records associated with appointments.

```text
consultations
├── id (PK)
├── appointment_id (FK → appointments.id)
└── ...
```

---

## prescriptions and medications

The prescription functionality is represented through prescription and medication-related entities.

```text
prescriptions
├── id (PK)
├── appointment_id (FK → appointments.id)
└── ...

medications
├── id (PK)
├── prescription_id (FK → prescriptions.id)
└── ...
```

---

## follow_ups

Stores follow-up information after consultations.

```text
follow_ups
├── id (PK)
├── appointment_id (FK → appointments.id)
└── ...
```

> The exact columns and constraints should be treated as defined by the SQLAlchemy models in `backend/models/`.

---

# 8. Authentication API

All protected endpoints require a JWT access token.

## Register

```http
POST /api/auth/register
```

Example:

```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "Password@123",
    "role": "patient"
}
```

---

## Login

```http
POST /api/auth/login
```

Example:

```json
{
    "email": "john@example.com",
    "password": "Password@123"
}
```

The response contains:

```json
{
    "message": "Login successful",
    "access_token": "JWT_TOKEN"
}
```

Use this token for protected requests.

In Postman:

```text
Authorization → Bearer Token → <access_token>
```

---

## Current User

```http
GET /api/auth/me
```

Requires:

```text
Authorization: Bearer <JWT_TOKEN>
```

---

# 9. Appointment APIs

Base URL:

```text
http://127.0.0.1:5000/api/appointments
```

## Get available doctors

```http
GET /api/appointments/doctors
```

---

## Hold appointment slot

```http
POST /api/appointments/hold
```

Example:

```json
{
    "doctor_id": 1,
    "appointment_date": "2026-08-25T10:00:00"
}
```

The slot is temporarily held before final booking.

---

## Confirm appointment

```http
POST /api/appointments/
```

Example:

```json
{
    "doctor_id": 1,
    "appointment_date": "2026-08-25T10:00:00",
    "reason": "Regular consultation",
    "hold_id": 10
}
```

---

## Patient appointments

```http
GET /api/appointments/
```

---

## Single appointment

```http
GET /api/appointments/<appointment_id>
```

---

## Cancel appointment

```http
DELETE /api/appointments/<appointment_id>
```

---

## Doctor appointments

```http
GET /api/appointments/doctor
```

---

# 10. Symptom and AI Summary Feature

One of the main AI features of the project is the pre-visit symptom summarization workflow.

The complete workflow is:

```text
Patient
   │
   │ submits symptoms
   ▼
POST /api/symptoms/
   │
   ▼
Store symptoms in PostgreSQL
   │
   ▼
AI Summary Service
   │
   ▼
Ollama
   │
   ▼
Llama 3.2 3B
   │
   ▼
Structured JSON response
   │
   ▼
Validate AI response
   │
   ▼
Store AI summary in PostgreSQL
   │
   ▼
Doctor retrieves appointment
   │
   ▼
Symptoms + AI summary
```

---

# 11. Ollama Setup

Install Ollama and verify:

```powershell
ollama --version
```

Download the model:

```powershell
ollama pull llama3.2:3b
```

Check installed models:

```powershell
ollama list
```

The application uses Ollama to run the Llama 3.2 3B model locally.

The Ollama service normally runs on:

```text
http://127.0.0.1:11434
```

If Ollama is already running, do **not** start another server manually.

---

# 12. LLM Prompt

The AI summary service asks the model to generate a structured pre-visit summary.

The prompt requires exactly these fields:

```json
{
    "urgency_level": "Low",
    "chief_complaint": "",
    "suggested_question_1": "",
    "suggested_question_2": "",
    "suggested_question_3": ""
}
```

The urgency level must be one of:

```text
Low
Medium
High
```

The model is explicitly instructed:

* Do not diagnose the patient.
* Do not prescribe treatment.
* Generate a concise chief complaint.
* Generate exactly three questions for the doctor.
* Return JSON only.

The application validates the response before storing it in PostgreSQL.

---

# 13. AI Failure Handling

The AI service is treated as a supporting feature rather than a requirement for storing patient symptoms.

If the LLM fails:

```text
Patient symptoms
      │
      ▼
PostgreSQL
      │
      ├── Saved successfully
      │
      ▼
AI generation
      │
      └── Failure
            │
            ▼
Symptoms remain stored
```

The API returns a successful symptom submission response while indicating that the AI summary could not be generated.

This prevents temporary LLM failures from causing loss of patient-submitted information.

---

# 14. Doctor Symptom + AI Summary API

A doctor can retrieve the symptoms associated with a specific appointment.

```http
GET /api/symptoms/appointment/<appointment_id>
```

The endpoint requires a doctor JWT.

Example:

```text
Authorization: Bearer <doctor_access_token>
```

The endpoint verifies that the appointment belongs to the authenticated doctor before returning patient information.

The response contains the submitted symptoms and the associated AI-generated pre-visit summary.

---

# 15. Double-Booking Prevention

The appointment system uses multiple layers of protection.

### Application-level validation

Before booking, the system checks whether the requested slot is already scheduled.

### Slot holds

Patients temporarily hold a slot before confirming an appointment.

### Hold expiration

Expired holds are removed before new holds are created.

### Database-level protection

A database uniqueness constraint/index protects the system against concurrent requests attempting to reserve the same doctor and appointment time.

Therefore, even if two patients attempt to book the same slot simultaneously, the database provides the final protection against duplicate bookings.

---

# 16. Doctor Leave Conflict Handling

Before a slot can be held or booked, the system checks whether the doctor has leave on the requested date.

```text
Requested appointment
        │
        ▼
Doctor leave check
        │
   ┌────┴────┐
   │         │
On leave   Available
   │         │
 Reject     Continue
```

If the doctor is on leave, the request returns a conflict response and the appointment is not created.

---

# 17. Slot Hold Mechanism

The slot hold system prevents a patient from losing a slot while completing the booking process.

```text
Patient selects slot
        │
        ▼
Temporary hold
        │
        ├── Booking confirmed → Appointment created
        │
        └── Hold expires → Slot becomes available
```

The hold contains an expiration timestamp.

The final appointment creation verifies:

* Hold belongs to the patient.
* Hold belongs to the selected doctor.
* Hold matches the selected appointment time.
* Hold has not expired.

---

# 18. Running the Application

Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

Start Flask:

```powershell
python -m flask --app backend.app run
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

# 19. Testing with Postman

The APIs can be tested using Postman.

Recommended testing order:

```text
1. Register patient
2. Register/login doctor
3. Login patient
4. Get doctors
5. Configure/check availability
6. Hold appointment slot
7. Confirm appointment
8. Submit patient symptoms
9. Generate AI pre-visit summary
10. Login as doctor
11. Retrieve appointment symptoms + AI summary
12. Test cancellation
```

For protected endpoints:

```text
Authorization
    ↓
Bearer Token
    ↓
<JWT access token>
```

---

# 20. Google Calendar Integration

Google Calendar integration can be used to create calendar events after successful appointment booking.

## Google Cloud setup

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable the **Google Calendar API**.
4. Configure the OAuth consent screen.
5. Create OAuth 2.0 credentials.
6. Configure the appropriate redirect URI.
7. Download the OAuth credentials file.
8. Store credentials securely and do not commit secrets to GitHub.

A typical flow is:

```text
Appointment booked
        │
        ▼
Create Google Calendar event
        │
        ├── Success → store event information
        │
        └── Failure → appointment remains booked
                       and failure is handled separately
```

Calendar integration should not invalidate an already successful database transaction.

---

# 21. Security Considerations

The project follows several basic security practices:

* Passwords are stored as hashes rather than plaintext.
* JWT authentication protects private APIs.
* Patient and doctor ownership checks prevent unauthorized appointment access.
* Environment variables are used for secrets and database credentials.
* `.env` is excluded from Git.
* AI functionality does not intentionally provide diagnosis or treatment recommendations.
* Sensitive configuration should never be committed to the repository.

---

# 22. API Error Handling

The API uses HTTP status codes to communicate errors.

Common responses include:

| Status | Meaning                            |
| ------ | ---------------------------------- |
| 200    | Successful request                 |
| 201    | Resource created                   |
| 400    | Invalid request                    |
| 401    | Authentication required/invalid    |
| 403    | Access denied                      |
| 404    | Resource not found                 |
| 409    | Conflict, such as unavailable slot |
| 500    | Server/internal error              |

---

# 23. Current Implementation

Implemented backend functionality includes:

* Flask backend
* PostgreSQL database
* SQLAlchemy models
* JWT authentication
* Patient/doctor user separation
* Appointment creation
* Appointment cancellation
* Doctor availability
* Working hours
* Doctor leave handling
* Temporary appointment slot holds
* Database-level double-booking protection
* Patient symptom submission
* Local LLM integration using Ollama
* Llama 3.2 3B model
* AI pre-visit summary generation
* AI response validation
* PostgreSQL persistence of AI summaries
* Doctor retrieval of appointment symptoms
* Notifications
* Reminder infrastructure
* Consultation infrastructure
* Prescription infrastructure
* Follow-up infrastructure

---

# 24. Repository

GitHub repository:

https://github.com/WilhelminaSA/healthcare-appointment-manager

---

# 25. License

This project was developed as a software engineering project for evaluation and demonstration purposes.
