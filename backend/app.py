
import hashlib
import os
import secrets
import smtplib
import sys
from datetime import datetime, timedelta, date, timezone
from email.message import EmailMessage
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
DATABASE_URL = os.getenv("DATABASE_URL")

def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured. Copy backend/.env.example to backend/.env and set it.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def json_error(message, status=400):
    return jsonify({"error": message}), status

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with db() as conn:
        return conn.execute(
            "SELECT id,email,role,full_name,email_verified,created_at FROM users WHERE id=%s",
            (uid,)
        ).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return json_error("Authentication required", 401)
        if not user["email_verified"]:
            return json_error("Email verification required", 403)
        return fn(user, *args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(user, *args, **kwargs):
        if user["role"] != "admin":
            return json_error("Administrator access required", 403)
        return fn(user, *args, **kwargs)
    return wrapper

def audit(user, action, entity_type=None, entity_id=None, details=None, old_value=None, new_value=None):
    with db() as conn:
        conn.execute(
            """INSERT INTO audit_logs(user_id,user_name,action,entity_type,entity_id,old_value,new_value,details)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user["id"], user.get("full_name"), action, entity_type, str(entity_id) if entity_id else None,
             old_value, new_value, details)
        )
        conn.commit()

def send_message(to, subject, body):
    host = os.getenv("SMTP_HOST")
    if not host:
        app.logger.warning("SMTP not configured. Message for %s:\n%s", to, body)
        return
    msg = EmailMessage()
    msg["From"] = os.getenv("MAIL_FROM", "no-reply@example.com")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if os.getenv("SMTP_USE_TLS", "1") == "1":
            smtp.starttls()
        if os.getenv("SMTP_USERNAME"):
            smtp.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD", ""))
        smtp.send_message(msg)

def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()

def grade_for(score):
    score = float(score)
    if score >= 70: return ("A", 5)
    if score >= 60: return ("B", 4)
    if score >= 50: return ("C", 3)
    if score >= 45: return ("D", 2)
    if score >= 40: return ("E", 1)
    return ("F", 0)

def student_query(extra_where="", params=()):
    q = """
    SELECT s.*, u.name AS university_name, f.name AS faculty_name,
           d.name AS department_name, p.name AS programme_name,
           a.session_name
    FROM students s
    LEFT JOIN universities u ON u.id=s.university_id
    LEFT JOIN faculties f ON f.id=s.faculty_id
    LEFT JOIN departments d ON d.id=s.department_id
    LEFT JOIN programmes p ON p.id=s.programme_id
    LEFT JOIN academic_sessions a ON a.id=s.academic_session_id
    """
    if extra_where:
        q += " WHERE " + extra_where
    q += " ORDER BY s.created_at DESC"
    with db() as conn:
        return conn.execute(q, params).fetchall()

@app.get("/api/health")
def health():
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as exc:
        return json_error(str(exc), 503)

@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email","")).strip().lower()
    password = str(data.get("password",""))
    full_name = str(data.get("full_name","")).strip() or None
    if "@" not in email or len(password) < 8:
        return json_error("Enter a valid email and a password of at least 8 characters.")
    otp = f"{secrets.randbelow(1_000_000):06d}"
    with db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=%s", (email,)).fetchone():
            return json_error("An account with that email already exists.", 409)
        cur = conn.execute(
            """INSERT INTO users(email,password_hash,role,full_name,otp_hash,otp_expires_at)
               VALUES(%s,%s,'user',%s,%s,%s) RETURNING id""",
            (email, generate_password_hash(password), full_name, token_hash(otp),
             datetime.now(timezone.utc)+timedelta(minutes=10))
        )
        user_id = cur.fetchone()["id"]
        conn.commit()
    send_message(email, "Student Management System verification code",
                 f"Your verification code is {otp}. It expires in 10 minutes.")
    return jsonify({"message":"Account created. Check your email for the 6-digit verification code.",
                    "development_otp": otp if not os.getenv("SMTP_HOST") else None})

@app.post("/api/auth/verify")
def verify():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email","")).strip().lower()
    otp = str(data.get("otp","")).strip()
    with db() as conn:
        row = conn.execute(
            "SELECT id,otp_hash,otp_expires_at FROM users WHERE email=%s", (email,)
        ).fetchone()
        if not row or not row["otp_hash"] or row["otp_expires_at"] < datetime.now(timezone.utc) or token_hash(otp) != row["otp_hash"]:
            return json_error("Invalid or expired verification code.")
        conn.execute("UPDATE users SET email_verified=TRUE,otp_hash=NULL,otp_expires_at=NULL WHERE id=%s",
                     (row["id"],))
        conn.commit()
    session.clear()
    session["user_id"] = row["id"]
    return jsonify({"message":"Email verified."})

@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email","")).strip().lower()
    password = str(data.get("password",""))
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=%s", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return json_error("Invalid email or password.", 401)
    if not user["email_verified"]:
        return json_error("Please verify your email before logging in.", 403)
    session.clear()
    session["user_id"] = user["id"]
    audit(user, "LOGIN", "User", user["id"])
    return jsonify({"message":"Logged in."})

@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message":"Logged out."})

@app.get("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"authenticated":False})
    return jsonify({"authenticated":True,"user":user})

@app.post("/api/auth/forgot")
def forgot():
    data=request.get_json(silent=True) or {}
    email=str(data.get("email","")).strip().lower()
    with db() as conn:
        user=conn.execute("SELECT id FROM users WHERE email=%s",(email,)).fetchone()
        if user:
            raw=secrets.token_urlsafe(48)
            conn.execute("""UPDATE users SET reset_token_hash=%s,reset_expires_at=%s WHERE id=%s""",
                         (token_hash(raw),datetime.now(timezone.utc)+timedelta(minutes=30),user["id"]))
            conn.commit()
            link=f"{request.host_url.rstrip('/')}/reset-password.html?token={raw}"
            send_message(email,"Password reset",f"Open this link within 30 minutes:\n{link}")
    return jsonify({"message":"If an account exists with that email, a reset link has been sent."})

@app.post("/api/auth/reset")
def reset():
    data=request.get_json(silent=True) or {}
    token=str(data.get("token",""))
    password=str(data.get("password",""))
    if len(password)<8 or not token:
        return json_error("Invalid reset request.")
    with db() as conn:
        row=conn.execute("""SELECT id,reset_expires_at FROM users WHERE reset_token_hash=%s""",
                         (token_hash(token),)).fetchone()
        if not row or not row["reset_expires_at"] or row["reset_expires_at"] < datetime.now(timezone.utc):
            return json_error("Reset link is invalid or expired.")
        conn.execute("""UPDATE users SET password_hash=%s,reset_token_hash=NULL,reset_expires_at=NULL WHERE id=%s""",
                     (generate_password_hash(password),row["id"]))
        conn.commit()
    return jsonify({"message":"Password reset successfully."})

@app.get("/api/dashboard")
@login_required
def dashboard(user):
    with db() as conn:
        total=conn.execute("SELECT COUNT(*) AS n FROM students").fetchone()["n"]
        statuses=conn.execute("SELECT student_status,COUNT(*) AS n FROM students GROUP BY student_status").fetchall()
        counts={r["student_status"]:r["n"] for r in statuses}
        collected=conn.execute("SELECT COALESCE(SUM(amount_paid),0) AS n FROM payments").fetchone()["n"]
        due=conn.execute("SELECT COALESCE(SUM(amount_due),0) AS n FROM payments").fetchone()["n"]
        faculties=conn.execute("SELECT COUNT(*) AS n FROM faculties").fetchone()["n"]
        departments=conn.execute("SELECT COUNT(*) AS n FROM departments").fetchone()["n"]
        programmes=conn.execute("SELECT COUNT(*) AS n FROM programmes").fetchone()["n"]
        hostel=conn.execute("SELECT COUNT(*) AS n FROM accommodations WHERE status='Allocated'").fetchone()["n"]
        pending=conn.execute("SELECT COUNT(*) AS n FROM admissions WHERE clearance_status<>'Cleared'").fetchone()["n"]
        recent=conn.execute("""SELECT id,first_name,middle_name,last_name,registration_number,
                                      level,student_status
                               FROM students ORDER BY created_at DESC LIMIT 5""").fetchall()
    return jsonify({
        "total":total,"active":counts.get("Active",0),"graduated":counts.get("Graduated",0),
        "suspended":counts.get("Suspended",0),"inactive":counts.get("Inactive",0),
        "withdrawn":counts.get("Withdrawn",0),"faculties":faculties,"departments":departments,
        "programmes":programmes,"hostel_allocated":hostel,"pending_clearance":pending,
        "collected":float(collected or 0),"outstanding":float(due or 0)-float(collected or 0),
        "students":recent
    })

@app.get("/api/students")
@login_required
def students(user):
    q=request.args.get("q","").strip()
    status=request.args.get("status","All")
    where=[]; params=[]
    if q:
        where.append("(LOWER(s.first_name||' '||COALESCE(s.middle_name,'')||' '||s.last_name) LIKE %s OR LOWER(s.registration_number) LIKE %s)")
        term=f"%{q.lower()}%"; params += [term,term]
    if status!="All":
        where.append("s.student_status=%s"); params.append(status)
    rows=student_query(" AND ".join(where),params)
    return jsonify(rows)

@app.get("/api/students/<int:student_id>")
@login_required
def get_student(user,student_id):
    with db() as conn:
        s=conn.execute("""SELECT s.*,u.name university_name,f.name faculty_name,d.name department_name,
                                 p.name programme_name,a.session_name
                          FROM students s
                          LEFT JOIN universities u ON u.id=s.university_id
                          LEFT JOIN faculties f ON f.id=s.faculty_id
                          LEFT JOIN departments d ON d.id=s.department_id
                          LEFT JOIN programmes p ON p.id=s.programme_id
                          LEFT JOIN academic_sessions a ON a.id=s.academic_session_id
                          WHERE s.id=%s""",(student_id,)).fetchone()
        if not s: return json_error("Student not found.",404)
        contact=conn.execute("SELECT * FROM student_contacts WHERE student_id=%s",(student_id,)).fetchone()
        admission=conn.execute("SELECT * FROM admissions WHERE student_id=%s",(student_id,)).fetchone()
        accommodation=conn.execute("SELECT * FROM accommodations WHERE student_id=%s ORDER BY id DESC LIMIT 1",(student_id,)).fetchone()
    return jsonify({"student":s,"contact":contact,"admission":admission,"accommodation":accommodation})

@app.post("/api/students")
@admin_required
def create_student(user):
    data=request.get_json(silent=True) or {}
    required=["registration_number","first_name","last_name"]
    if any(not str(data.get(k,"")).strip() for k in required):
        return json_error("Registration number, first name and last name are required.")
    with db() as conn:
        try:
            cur=conn.execute("""INSERT INTO students
              (registration_number,first_name,middle_name,last_name,photo_url,gender,date_of_birth,
               university_id,faculty_id,department_id,programme_id,level,academic_session_id,student_status)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
              (data["registration_number"],data["first_name"],data.get("middle_name"),data["last_name"],
               data.get("photo_url"),data.get("gender"),data.get("date_of_birth") or None,
               data.get("university_id") or None,data.get("faculty_id") or None,data.get("department_id") or None,
               data.get("programme_id") or None,int(data.get("level",100)),data.get("academic_session_id") or None,
               data.get("student_status","Active")))
            sid=cur.fetchone()["id"]
            conn.commit()
        except psycopg.errors.UniqueViolation:
            conn.rollback(); return json_error("Registration number already exists.",409)
    audit(user,"CREATE","Student",sid,details="Student created")
    return jsonify({"id":sid}),201

@app.put("/api/students/<int:student_id>")
@admin_required
def update_student(user,student_id):
    data=request.get_json(silent=True) or {}
    allowed=["first_name","middle_name","last_name","photo_url","gender","date_of_birth",
             "university_id","faculty_id","department_id","programme_id","level","academic_session_id","student_status"]
    fields=[]; vals=[]
    for k in allowed:
        if k in data:
            fields.append(f"{k}=%s"); vals.append(data[k] if data[k] != "" else None)
    if not fields: return json_error("No editable fields supplied.")
    vals.append(student_id)
    with db() as conn:
        old=conn.execute("SELECT * FROM students WHERE id=%s",(student_id,)).fetchone()
        if not old: return json_error("Student not found.",404)
        conn.execute("UPDATE students SET "+",".join(fields)+",updated_at=NOW() WHERE id=%s",vals)
        conn.commit()
    audit(user,"UPDATE","Student",student_id,old_value=str(dict(old)),new_value=str(data))
    return jsonify({"message":"Student updated."})

@app.get("/api/students/<int:student_id>/overview")
@login_required
def student_overview(user,student_id):
    with db() as conn:
        results=conn.execute("""SELECT r.*,c.course_code,c.course_title,c.credit_units
                                FROM results r JOIN courses c ON c.id=r.course_id
                                WHERE r.student_id=%s ORDER BY r.academic_session_id,r.semester_id""",(student_id,)).fetchall()
        regs=conn.execute("""SELECT cr.*,c.course_code,c.course_title,c.credit_units,c.level
                             FROM course_registrations cr JOIN courses c ON c.id=cr.course_id
                             WHERE cr.student_id=%s ORDER BY cr.id""",(student_id,)).fetchall()
        pays=conn.execute("SELECT * FROM payments WHERE student_id=%s ORDER BY id DESC",(student_id,)).fetchall()
        att=conn.execute("""SELECT a.*,c.course_code,c.course_title FROM attendance a
                            JOIN courses c ON c.id=a.course_id WHERE a.student_id=%s ORDER BY a.id DESC""",(student_id,)).fetchall()
        admission=conn.execute("SELECT * FROM admissions WHERE student_id=%s",(student_id,)).fetchone()
    total_cu=sum(float(r["credit_units"] or 0) for r in results)
    total_qp=sum(float(grade_for(r["score"])[1])*float(r["credit_units"] or 0) for r in results)
    total_classes=sum(r["total_classes"] for r in att); attended=sum(r["classes_attended"] for r in att)
    due=sum(float(p["amount_due"]) for p in pays); paid=sum(float(p["amount_paid"]) for p in pays)
    return jsonify({
        "results":results,"registrations":regs,"payments":pays,"attendance":att,"admission":admission,
        "gpa": round(total_qp/total_cu,2) if total_cu else 0,
        "cgpa": round(total_qp/total_cu,2) if total_cu else 0,
        "attendance_percentage": round(attended/total_classes*100) if total_classes else 0,
        "total_due":due,"total_paid":paid,"balance":due-paid
    })

@app.get("/api/catalog")
@login_required
def catalog(user):
    with db() as conn:
        data={}
        for key,table in [("universities","universities"),("faculties","faculties"),("departments","departments"),
                           ("programmes","programmes"),("sessions","academic_sessions"),("semesters","semesters"),
                           ("courses","courses")]:
            data[key]=conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    return jsonify(data)

@app.post("/api/registrations")
@admin_required
def create_registration(user):
    d=request.get_json(silent=True) or {}
    required=["student_id","course_id","academic_session_id","semester_id"]
    if any(d.get(k) is None for k in required): return json_error("Student, course, session and semester are required.")
    with db() as conn:
        try:
            cur=conn.execute("""INSERT INTO course_registrations(student_id,course_id,academic_session_id,semester_id,status)
                               VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                             (d["student_id"],d["course_id"],d["academic_session_id"],d["semester_id"],d.get("status","Registered")))
            rid=cur.fetchone()["id"]; conn.commit()
        except psycopg.errors.UniqueViolation:
            conn.rollback(); return json_error("That course is already registered for this session and semester.",409)
    audit(user,"CREATE","CourseRegistration",rid)
    return jsonify({"id":rid}),201

@app.post("/api/results")
@admin_required
def create_result(user):
    d=request.get_json(silent=True) or {}
    required=["student_id","course_id","academic_session_id","semester_id","score"]
    if any(d.get(k) is None for k in required): return json_error("Student, course, session, semester and score are required.")
    score=float(d["score"])
    if score<0 or score>100: return json_error("Score must be between 0 and 100.")
    with db() as conn:
        course=conn.execute("SELECT credit_units FROM courses WHERE id=%s",(d["course_id"],)).fetchone()
        if not course: return json_error("Course not found.",404)
        try:
            cur=conn.execute("""INSERT INTO results(student_id,course_id,academic_session_id,semester_id,score,recorded_by_id)
                               VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                             (d["student_id"],d["course_id"],d["academic_session_id"],d["semester_id"],score,user["id"]))
            rid=cur.fetchone()["id"]; conn.commit()
        except psycopg.errors.UniqueViolation:
            conn.rollback(); return json_error("A result already exists for that course/session/semester.",409)
    grade,gp=grade_for(score)
    audit(user,"CREATE","Result",rid,details=f"{grade} ({gp})")
    return jsonify({"id":rid,"grade":grade,"grade_point":gp,"quality_points":gp*int(course["credit_units"])}),201

@app.post("/api/attendance")
@admin_required
def create_attendance(user):
    d=request.get_json(silent=True) or {}
    try:
        total=int(d["total_classes"]); attended=int(d["classes_attended"])
    except (KeyError,TypeError,ValueError): return json_error("Attendance totals are required.")
    if total<0 or attended<0 or attended>total: return json_error("Attendance values are invalid.")
    with db() as conn:
        try:
            cur=conn.execute("""INSERT INTO attendance(student_id,course_id,academic_session_id,semester_id,total_classes,classes_attended)
                               VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                             (d["student_id"],d["course_id"],d["academic_session_id"],d["semester_id"],total,attended))
            aid=cur.fetchone()["id"]; conn.commit()
        except psycopg.errors.UniqueViolation:
            conn.rollback(); return json_error("Attendance already exists for that course/session/semester.",409)
    audit(user,"CREATE","Attendance",aid)
    return jsonify({"id":aid,"percentage":round(attended/total*100) if total else 0}),201

@app.post("/api/payments")
@admin_required
def create_payment(user):
    d=request.get_json(silent=True) or {}
    try: due=float(d["amount_due"]); paid=float(d.get("amount_paid",0))
    except (KeyError,TypeError,ValueError): return json_error("Amount due is required.")
    if due<0 or paid<0: return json_error("Amounts cannot be negative.")
    status="Paid" if due>0 and paid>=due else ("Partially Paid" if paid>0 else "Pending")
    with db() as conn:
        cur=conn.execute("""INSERT INTO payments(student_id,academic_session_id,semester_id,fee_type,amount_due,amount_paid,
                           payment_date,payment_reference,payment_method,payment_status,recorded_by_id)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                         (d["student_id"],d["academic_session_id"],d.get("semester_id") or None,d.get("fee_type","Tuition"),
                          due,paid,d.get("payment_date") or date.today(),d.get("payment_reference"),
                          d.get("payment_method"),status,user["id"]))
        pid=cur.fetchone()["id"]; conn.commit()
    audit(user,"CREATE","Payment",pid,details=f"₦{paid:,.2f} paid")
    return jsonify({"id":pid,"status":status}),201

@app.post("/api/admissions")
@admin_required
def save_admission(user):
    d=request.get_json(silent=True) or {}
    with db() as conn:
        conn.execute("""INSERT INTO admissions(student_id,admission_date,admission_type,admission_session,admission_number,
                       graduation_status,clearance_status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(student_id) DO UPDATE SET admission_date=EXCLUDED.admission_date,
                       admission_type=EXCLUDED.admission_type,admission_session=EXCLUDED.admission_session,
                       admission_number=EXCLUDED.admission_number,graduation_status=EXCLUDED.graduation_status,
                       clearance_status=EXCLUDED.clearance_status""",
                     (d["student_id"],d.get("admission_date") or date.today(),d.get("admission_type","UTME"),
                      d.get("admission_session"),d.get("admission_number"),d.get("graduation_status","Undergraduate"),
                      d.get("clearance_status","Not Cleared")))
        conn.commit()
    audit(user,"UPSERT","Admission",d["student_id"])
    return jsonify({"message":"Admission record saved."})

@app.post("/api/accommodations")
@admin_required
def save_accommodation(user):
    d=request.get_json(silent=True) or {}
    with db() as conn:
        cur=conn.execute("""INSERT INTO accommodations(student_id,hostel_name,block,room_number,bed_space,
                       academic_session_id,allocation_date,status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                     (d["student_id"],d["hostel_name"],d.get("block"),d.get("room_number"),d.get("bed_space"),
                      d.get("academic_session_id") or None,d.get("allocation_date") or date.today(),d.get("status","Allocated")))
        aid=cur.fetchone()["id"]; conn.commit()
    audit(user,"CREATE","Accommodation",aid)
    return jsonify({"id":aid}),201

@app.get("/api/analytics")
@admin_required
def analytics(user):
    from analytics.analytics import build_student_risk_report
    try:
        report=build_student_risk_report(db)
        return jsonify(report)
    except Exception as exc:
        return json_error(f"Analytics could not be generated: {exc}",500)

@app.get("/api/audit")
@admin_required
def audit_list(user):
    with db() as conn:
        rows=conn.execute("""SELECT id,user_name,action,entity_type,entity_id,details,created_at
                             FROM audit_logs ORDER BY created_at DESC LIMIT 100""").fetchall()
    return jsonify(rows)

@app.get("/api/catalog/<string:kind>")
@login_required
def catalog_kind(user,kind):
    allowed={"universities":"universities","faculties":"faculties","departments":"departments",
             "programmes":"programmes","sessions":"academic_sessions","semesters":"semesters","courses":"courses"}
    table=allowed.get(kind)
    if not table: return json_error("Unknown catalog.",404)
    with db() as conn:
        rows=conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    return jsonify(rows)

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR,"index.html")

@app.route("/<path:path>")
def static_files(path):
    full=os.path.join(FRONTEND_DIR,path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIR,path)
    return send_from_directory(FRONTEND_DIR,"index.html")

if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=os.getenv("FLASK_DEBUG","0")=="1")
