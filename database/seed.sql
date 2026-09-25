
-- Optional development seed data.
INSERT INTO academic_sessions(session_name,is_current)
VALUES ('2024/2025',TRUE)
ON CONFLICT (session_name) DO NOTHING;

INSERT INTO universities(name,code,address)
VALUES ('Veritas University','VERITAS','Abuja, Nigeria')
ON CONFLICT (name) DO NOTHING;

INSERT INTO faculties(name,university_id)
SELECT 'Faculty of Natural and Applied Science',id FROM universities WHERE name='Veritas University'
ON CONFLICT DO NOTHING;

INSERT INTO departments(name,faculty_id)
SELECT 'Computer Science',f.id
FROM faculties f JOIN universities u ON u.id=f.university_id
WHERE f.name='Faculty of Natural and Applied Science' AND u.name='Veritas University'
ON CONFLICT DO NOTHING;

INSERT INTO programmes(name,programme_code,degree_type,department_id)
SELECT 'B.Sc. Computer Science','CSC','B.Sc.',
       d.id
FROM departments d JOIN faculties f ON f.id=d.faculty_id
WHERE d.name='Computer Science'
ON CONFLICT DO NOTHING;

INSERT INTO semesters(name,is_current)
VALUES ('First Semester',TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO courses(course_code,course_title,credit_units,department_id,programme_id,level,semester_id)
SELECT x.code,x.title,x.units,d.id,p.id,x.level,s.id
FROM (VALUES
 ('CSC 101','Computer Programming I',3,100),
 ('MTH 101','Elementary Mathematics I',3,100),
 ('STA 111','Descriptive Statistics',2,100),
 ('BIO 101','General Biology',3,100),
 ('VUA THE 112','Communication in English',2,100),
 ('CSC 103','Introduction to Computing',2,100),
 ('CHEM 101','General Chemistry',3,100),
 ('VUA THE 101','Use of English',1,100),
 ('PHY 101','General Physics I',3,100)
) AS x(code,title,units,level)
JOIN departments d ON d.name='Computer Science'
JOIN programmes p ON p.department_id=d.id
JOIN semesters s ON s.name='First Semester'
ON CONFLICT (course_code) DO UPDATE SET course_title=EXCLUDED.course_title,credit_units=EXCLUDED.credit_units;

INSERT INTO students(
    registration_number,first_name,last_name,photo_url,gender,university_id,faculty_id,
    department_id,programme_id,level,academic_session_id,student_status
)
SELECT 'VUG/CSC/24/13099','Victory','Philip','/victory-philip.jpg','Female',u.id,f.id,d.id,p.id,100,a.id,'Active'
FROM universities u
JOIN faculties f ON f.university_id=u.id
JOIN departments d ON d.faculty_id=f.id
JOIN programmes p ON p.department_id=d.id
JOIN academic_sessions a ON a.session_name='2024/2025'
WHERE u.name='Veritas University'
  AND f.name='Faculty of Natural and Applied Science'
  AND d.name='Computer Science'
  AND p.name='B.Sc. Computer Science'
ON CONFLICT (registration_number) DO UPDATE SET photo_url=EXCLUDED.photo_url;

INSERT INTO student_contacts(
    student_id,email,phone,residential_address,state,emergency_contact_name,emergency_contact_phone,emergency_contact_relationship
)
SELECT s.id,'philipvictory740@gmail.com','07037691494','EFAB Estate, Jabi, Abuja','Abuja/FCT','Peacemark Philip','08139134905','Sister'
FROM students s
WHERE s.registration_number='VUG/CSC/24/13099'
ON CONFLICT (student_id) DO UPDATE SET email=EXCLUDED.email,phone=EXCLUDED.phone,
    residential_address=EXCLUDED.residential_address,state=EXCLUDED.state,
    emergency_contact_name=EXCLUDED.emergency_contact_name,
    emergency_contact_phone=EXCLUDED.emergency_contact_phone,
    emergency_contact_relationship=EXCLUDED.emergency_contact_relationship;

INSERT INTO payments(
    student_id,academic_session_id,semester_id,fee_type,amount_due,amount_paid,
    payment_date,payment_reference,payment_method,payment_status
)
SELECT s.id,a.id,sem.id,'Tuition',2100000,2100000,'2024-09-08','SEED-TUITION-001','Bank Transfer','Paid'
FROM students s
JOIN academic_sessions a ON a.session_name='2024/2025'
JOIN semesters sem ON sem.name='First Semester'
WHERE s.registration_number='VUG/CSC/24/13099'
  AND NOT EXISTS (
      SELECT 1 FROM payments p WHERE p.student_id=s.id AND p.payment_reference='SEED-TUITION-001'
  );

INSERT INTO accommodations(
    student_id,hostel_name,block,room_number,bed_space,academic_session_id,allocation_date,status
)
SELECT s.id,'Hostel A','A','20B','Wing B',a.id,'2024-09-05','Allocated'
FROM students s
JOIN academic_sessions a ON a.session_name='2024/2025'
WHERE s.registration_number='VUG/CSC/24/13099'
  AND NOT EXISTS (
      SELECT 1 FROM accommodations x WHERE x.student_id=s.id AND x.academic_session_id=a.id
  );

INSERT INTO admissions(
    student_id,admission_date,admission_type,admission_session,admission_number,graduation_status,clearance_status
)
SELECT s.id,'2024-08-12','UTME','2024/2025','VUG/CSC/24/13099','Undergraduate','Not Cleared'
FROM students s
WHERE s.registration_number='VUG/CSC/24/13099'
ON CONFLICT (student_id) DO NOTHING;

INSERT INTO course_registrations(student_id,course_id,academic_session_id,semester_id,status)
SELECT s.id,c.id,a.id,sem.id,'Registered'
FROM students s
JOIN courses c ON c.level=s.level
JOIN academic_sessions a ON a.session_name='2024/2025'
JOIN semesters sem ON sem.name='First Semester'
WHERE s.registration_number='VUG/CSC/24/13099'
ON CONFLICT (student_id,course_id,academic_session_id,semester_id) DO NOTHING;

INSERT INTO results(student_id,course_id,academic_session_id,semester_id,score)
SELECT cr.student_id,cr.course_id,cr.academic_session_id,cr.semester_id,85
FROM course_registrations cr
JOIN students s ON s.id=cr.student_id
WHERE s.registration_number='VUG/CSC/24/13099'
ON CONFLICT (student_id,course_id,academic_session_id,semester_id) DO NOTHING;

INSERT INTO attendance(student_id,course_id,academic_session_id,semester_id,total_classes,classes_attended)
SELECT cr.student_id,cr.course_id,cr.academic_session_id,cr.semester_id,10,7
FROM course_registrations cr
JOIN students s ON s.id=cr.student_id
WHERE s.registration_number='VUG/CSC/24/13099'
ON CONFLICT (student_id,course_id,academic_session_id,semester_id) DO NOTHING;
