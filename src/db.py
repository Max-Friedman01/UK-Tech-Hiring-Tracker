import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from models import Job

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    platform        TEXT NOT NULL,
    job_id          TEXT NOT NULL,
    board_id        TEXT NOT NULL,
    title           TEXT,
    location        TEXT,
    departments     TEXT,
    offices         TEXT,
    url             TEXT,
    updated_at      TEXT,
    first_published TEXT,
    content         TEXT,
    raw_json        TEXT,
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL,
    PRIMARY KEY (platform, job_id)
)
"""

UPSERT = """
INSERT INTO jobs (
    platform, job_id, board_id, title, location, departments, offices,
    url, updated_at, first_published, content, raw_json, first_seen, last_seen
)
VALUES (
    :platform, :job_id, :board_id, :title, :location, :departments, :offices,
    :url, :updated_at, :first_published, :content, :raw_json, :seen_at, :seen_at
)
ON CONFLICT (platform, job_id) DO UPDATE SET
    title           = excluded.title,
    location        = excluded.location,
    departments     = excluded.departments,
    offices         = excluded.offices,
    url             = excluded.url,
    updated_at      = excluded.updated_at,
    first_published = excluded.first_published,
    content         = excluded.content,
    raw_json        = excluded.raw_json,
    last_seen       = excluded.last_seen
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    return conn


def job_to_row(job: Job, seen_at: str) -> dict:
    row = asdict(job)
    row["departments"] = json.dumps(row["departments"])
    row["offices"] = json.dumps(row["offices"])
    row["seen_at"] = seen_at
    return row


def save_jobs(conn: sqlite3.Connection, jobs: list[Job], seen_at: str) -> None:
    rows = [job_to_row(job, seen_at) for job in jobs]
    with conn:
        conn.executemany(UPSERT, rows)


def count_jobs(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

def load_job_texts(conn: sqlite3.Connection) -> list[tuple]:
    query = "SELECT job_id, title, location, departments, offices, content FROM jobs"
    return conn.execute(query).fetchall()