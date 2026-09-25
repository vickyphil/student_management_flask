# Student Management System — Flask + PostgreSQL

This is the complete native replacement of the supplied Base44/React application.

## Required stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python + Flask
- Database: SQL + PostgreSQL
- Data science: NumPy + Pandas + scikit-learn

## What changed

The supplied project was a React/Vite application whose data and authentication were provided by Base44. The source contained `base44.entities.*` calls for students, results, attendance, payments, admissions and accommodation, and `base44.auth.*` calls for login, registration, OTP and password reset. It also used Base44's Vite plugin and platform-specific MCP OAuth consent flow.

Those pieces are removed here.

### Replacement mapping

| Original Base44 responsibility | Native replacement |
|---|---|
| Entity definitions | PostgreSQL tables in `database/schema.sql` |
| Entity list/filter/get | Flask JSON API + SQL queries |
| Authentication/session | Flask signed session + PostgreSQL `users` |
| Password hashing | Werkzeug password hashing |
| Registration OTP | Flask-generated OTP + optional SMTP |
| Password reset | PostgreSQL hashed reset token + optional SMTP |
| Audit logging | PostgreSQL `audit_logs` |
| GPA/grade/attendance/fee calculations | Python backend |
| Browser UI | Vanilla HTML/CSS/JavaScript |
| Browser routing | Hash routing in `frontend/app.js` |
| Analytics placeholder | NumPy/Pandas/scikit-learn risk analysis |
| Base44 MCP OAuth consent | Removed; it was platform-specific and unrelated to normal student-management operation |

## Setup

1. Install PostgreSQL and create a database, for example `student_management`.
2. Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` and `SECRET_KEY`.
3. From the project root:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r backend/requirements.txt
python backend/init_db.py
python backend/create_admin.py   # create the first administrator
python backend/app.py
```

4. Open `http://127.0.0.1:5000`.

## First account

Registration requires email verification. If SMTP is not configured, the verification code is printed in the Flask console and is also returned as `development_otp` in development responses.

For production, configure SMTP in `.env` so codes and password-reset links are actually emailed.

## Database

The schema preserves the original 19 entity concepts:

AcademicSession, Accommodation, Admission, Attendance, AuditLog, Course, CourseRegistration, Department, Faculty, GradingScale, Payment, Programme, Result, Semester, Student, StudentContact, University and User, with the entity relationships represented as PostgreSQL foreign keys.

Derived fields are deliberately not duplicated as editable columns:
- grade and grade point are calculated from score;
- quality points are grade point × credit units;
- GPA/CGPA are calculated from result records;
- attendance percentage is calculated from classes attended / total classes;
- payment balance is amount due − amount paid;
- payment status is derived when a payment is recorded.

## Notes on the original missing pieces

The supplied notepad referenced several files that were not actually included in it, including the original `Layout`, `AuthLayout`, `ProtectedRoute`, `StatCard`, `base44Client`, and several UI components. The original routes also left Courses, Results, Finance, Analytics, Audit and Settings as placeholders. This replacement therefore creates the required native shell, authentication, dashboard, students, courses, analytics and audit views rather than leaving those gaps as stubs.

The original Documents tab only called `window.print()` and explicitly said server-side PDF generation was future work. This version retains a print/save-as-PDF workflow without depending on Base44.

## Security

For production:
- use a strong random `SECRET_KEY`;
- serve over HTTPS;
- use secure cookie settings;
- configure SMTP;
- restrict database credentials;
- add CSRF protection appropriate to your deployment;
- use a reverse proxy such as Nginx/Gunicorn rather than Flask's development server.
