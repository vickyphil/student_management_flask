
-- Student Management System - PostgreSQL schema
-- the original platform entity definitions were converted to relational tables.
-- Derived values such as GPA, attendance percentage and payment balance are
-- calculated by the application rather than stored as editable values.

CREATE TABLE IF NOT EXISTS academic_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_name VARCHAR(20) NOT NULL UNIQUE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS universities (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50),
    address TEXT
);

CREATE TABLE IF NOT EXISTS faculties (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    university_id BIGINT NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    UNIQUE(name, university_id)
);

CREATE TABLE IF NOT EXISTS departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    faculty_id BIGINT NOT NULL REFERENCES faculties(id) ON DELETE RESTRICT,
    UNIQUE(name, faculty_id)
);

CREATE TABLE IF NOT EXISTS programmes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    programme_code VARCHAR(50),
    degree_type VARCHAR(30) NOT NULL DEFAULT 'B.Sc.',
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    UNIQUE(name, department_id)
);

CREATE TABLE IF NOT EXISTS semesters (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL CHECK (name IN ('First Semester','Second Semester','Harmattan','Rain')),
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    registration_number VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    photo_url TEXT,
    gender VARCHAR(20) CHECK (gender IN ('Male','Female') OR gender IS NULL),
    date_of_birth DATE,
    university_id BIGINT REFERENCES universities(id) ON DELETE SET NULL,
    faculty_id BIGINT REFERENCES faculties(id) ON DELETE SET NULL,
    department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    programme_id BIGINT REFERENCES programmes(id) ON DELETE SET NULL,
    level INTEGER NOT NULL DEFAULT 100 CHECK (level IN (100,200,300,400,500,600)),
    academic_session_id BIGINT REFERENCES academic_sessions(id) ON DELETE SET NULL,
    student_status VARCHAR(20) NOT NULL DEFAULT 'Active'
        CHECK (student_status IN ('Active','Inactive','Suspended','Graduated','Withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_contacts (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(50),
    residential_address TEXT,
    state VARCHAR(100),
    lga VARCHAR(100),
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    emergency_contact_relationship VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS courses (
    id BIGSERIAL PRIMARY KEY,
    course_code VARCHAR(50) NOT NULL UNIQUE,
    course_title VARCHAR(255) NOT NULL,
    credit_units INTEGER NOT NULL DEFAULT 2 CHECK (credit_units > 0),
    department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    programme_id BIGINT REFERENCES programmes(id) ON DELETE SET NULL,
    level INTEGER NOT NULL DEFAULT 100 CHECK (level IN (100,200,300,400,500,600)),
    semester_id BIGINT REFERENCES semesters(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS course_registrations (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    academic_session_id BIGINT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES semesters(id) ON DELETE RESTRICT,
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Registered'
        CHECK (status IN ('Registered','Dropped','Completed')),
    UNIQUE(student_id, course_id, academic_session_id, semester_id)
);

CREATE TABLE IF NOT EXISTS grading_scales (
    id BIGSERIAL PRIMARY KEY,
    grade CHAR(1) NOT NULL UNIQUE CHECK (grade IN ('A','B','C','D','E','F')),
    min_score NUMERIC(5,2) NOT NULL CHECK (min_score BETWEEN 0 AND 100),
    max_score NUMERIC(5,2) NOT NULL CHECK (max_score BETWEEN 0 AND 100),
    grade_point NUMERIC(4,2) NOT NULL CHECK (grade_point BETWEEN 0 AND 5),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (min_score <= max_score)
);

CREATE TABLE IF NOT EXISTS results (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    academic_session_id BIGINT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES semesters(id) ON DELETE RESTRICT,
    score NUMERIC(5,2) NOT NULL CHECK (score BETWEEN 0 AND 100),
    recorded_by_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, course_id, academic_session_id, semester_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    academic_session_id BIGINT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES semesters(id) ON DELETE RESTRICT,
    total_classes INTEGER NOT NULL CHECK (total_classes >= 0),
    classes_attended INTEGER NOT NULL CHECK (classes_attended >= 0 AND classes_attended <= total_classes),
    UNIQUE(student_id, course_id, academic_session_id, semester_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_session_id BIGINT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
    semester_id BIGINT REFERENCES semesters(id) ON DELETE SET NULL,
    fee_type VARCHAR(30) NOT NULL DEFAULT 'Tuition'
        CHECK (fee_type IN ('Tuition','Accommodation','Library','Lab','Medical','Other')),
    amount_due NUMERIC(14,2) NOT NULL CHECK (amount_due >= 0),
    amount_paid NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    payment_date DATE,
    payment_reference VARCHAR(100),
    payment_method VARCHAR(30)
        CHECK (payment_method IN ('Cash','Bank Transfer','Card','Online','Cheque') OR payment_method IS NULL),
    payment_status VARCHAR(30) NOT NULL DEFAULT 'Pending'
        CHECK (payment_status IN ('Paid','Partially Paid','Pending','Overdue','Refunded')),
    recorded_by_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admissions (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    admission_date DATE NOT NULL,
    admission_type VARCHAR(30) NOT NULL DEFAULT 'UTME'
        CHECK (admission_type IN ('UTME','Direct Entry','Transfer','Postgraduate')),
    admission_session VARCHAR(20),
    admission_number VARCHAR(100),
    graduation_status VARCHAR(20) NOT NULL DEFAULT 'Undergraduate'
        CHECK (graduation_status IN ('Undergraduate','Graduated','Withdrawn','Suspended')),
    clearance_status VARCHAR(20) NOT NULL DEFAULT 'Not Cleared'
        CHECK (clearance_status IN ('Cleared','Not Cleared','Pending'))
);

CREATE TABLE IF NOT EXISTS accommodations (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    hostel_name VARCHAR(255) NOT NULL,
    block VARCHAR(100),
    room_number VARCHAR(100),
    bed_space VARCHAR(100),
    academic_session_id BIGINT REFERENCES academic_sessions(id) ON DELETE SET NULL,
    allocation_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Allocated'
        CHECK (status IN ('Allocated','Vacated','Pending'))
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin','user')),
    full_name VARCHAR(255),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    otp_hash TEXT,
    otp_expires_at TIMESTAMPTZ,
    reset_token_hash TEXT,
    reset_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(255),
    action VARCHAR(30) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_name ON students(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(student_status);
CREATE INDEX IF NOT EXISTS idx_results_student ON results(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_course_reg_student ON course_registrations(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);

INSERT INTO grading_scales(grade,min_score,max_score,grade_point)
VALUES
('A',70,100,5),('B',60,69.99,4),('C',50,59.99,3),
('D',45,49.99,2),('E',40,44.99,1),('F',0,39.99,0)
ON CONFLICT (grade) DO NOTHING;

INSERT INTO semesters(name,is_current) VALUES ('First Semester',TRUE),('Second Semester',FALSE)
ON CONFLICT (name) DO NOTHING;
