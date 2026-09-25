# Student Management System - Flask + PostgreSQL

A self-contained student management system with a Flask backend, PostgreSQL database, and vanilla HTML, CSS, and JavaScript frontend.

## Required stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python + Flask
- Database: SQL + PostgreSQL
- Data science: NumPy + Pandas + scikit-learn

## Features

- Flask JSON API with signed-session authentication
- PostgreSQL storage for students, courses, results, attendance, payments, admissions, accommodation, and audit logs
- Password hashing, email verification, and password reset support
- GPA, grade, attendance, payment, and risk calculations
- Analytics powered by NumPy, Pandas, and scikit-learn
- Vanilla browser interface with hash-based routing

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

## Documents

The documents view supports the browser print dialog and save-as-PDF workflow without requiring a separate document service.

## Security

For production:
- use a strong random `SECRET_KEY`;
- serve over HTTPS;
- use secure cookie settings;
- configure SMTP;
- restrict database credentials;
- add CSRF protection appropriate to your deployment;
- use a reverse proxy such as Nginx/Gunicorn rather than Flask's development server.
