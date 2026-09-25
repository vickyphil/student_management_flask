
import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

BASE=Path(__file__).resolve().parent.parent
load_dotenv(BASE/"backend"/".env")
url=os.getenv("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not configured.")
schema=(BASE/"database"/"schema.sql").read_text(encoding="utf-8")
seed=(BASE/"database"/"seed.sql").read_text(encoding="utf-8")
with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(schema)
        cur.execute(seed)
    conn.commit()
print("Database initialized.")
