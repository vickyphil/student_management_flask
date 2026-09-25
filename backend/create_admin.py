
import os, sys
from getpass import getpass
import psycopg
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url=os.getenv("DATABASE_URL")
if not url: raise SystemExit("DATABASE_URL is not configured.")
email=input("Admin email: ").strip().lower()
name=input("Admin full name: ").strip()
password=getpass("Admin password (8+ chars): ")
if len(password)<8: raise SystemExit("Password must be at least 8 characters.")
with psycopg.connect(url) as conn:
    row=conn.execute("SELECT id FROM users WHERE email=%s",(email,)).fetchone()
    if row:
        conn.execute("UPDATE users SET role='admin',email_verified=TRUE,password_hash=%s,full_name=%s WHERE id=%s",
                     (generate_password_hash(password),name,row[0]))
    else:
        conn.execute("INSERT INTO users(email,password_hash,role,full_name,email_verified) VALUES(%s,%s,'admin',%s,TRUE)",
                     (email,generate_password_hash(password),name))
    conn.commit()
print("Administrator account ready.")
