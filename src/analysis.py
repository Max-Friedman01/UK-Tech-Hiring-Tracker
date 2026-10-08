import html
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORT_PATH = DATA_DIR / "analysis_report.txt"

TOP_N = 15

_NOT_BEFORE = r"(?<![A-Za-z0-9_])"
_NOT_AFTER = r"(?![A-Za-z0-9_+#])"


def _skill(pattern: str, ignore_case: bool = True) -> re.Pattern:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(_NOT_BEFORE + pattern + _NOT_AFTER, flags)


SKILLS = {
    "Python": _skill(r"python"),
    "Java": _skill(r"java"),
    "JavaScript": _skill(r"javascript"),
    "TypeScript": _skill(r"typescript"),
    "Go": _skill(r"(?:golang|Go)", ignore_case=False),
    "Rust": _skill(r"rust"),
    "C++": _skill(r"c\+\+"),
    "C#": _skill(r"c#"),
    "Kotlin": _skill(r"kotlin"),
    "Swift": _skill(r"swift"),
    "Ruby": _skill(r"ruby"),
    "PHP": _skill(r"php"),
    "Scala": _skill(r"scala"),
    "SQL": _skill(r"sql"),
    "PostgreSQL": _skill(r"postgres(?:ql)?"),
    "React": _skill(r"react"),
    "Node.js": _skill(r"node(?:\.js|js)?"),
    "AWS": _skill(r"aws"),
    "GCP": _skill(r"(?:gcp|google cloud)"),
    "Azure": _skill(r"azure"),
    "Docker": _skill(r"docker"),
    "Kubernetes": _skill(r"(?:kubernetes|k8s)"),
    "Terraform": _skill(r"terraform"),
    "Kafka": _skill(r"kafka"),
    "Spark": _skill(r"spark"),
    "Linux": _skill(r"linux"),
    "Machine learning": _skill(r"(?:machine learning|ML)"),
    "LLMs": _skill(r"(?:llms?|large language models?)"),
}

SENIORITY_LEVELS = [
    ("Intern", re.compile(r"\b(?:intern|internship|placement)\b", re.IGNORECASE)),
    ("Graduate", re.compile(r"\b(?:graduate|grad|new grad|entry[- ]level)\b", re.IGNORECASE)),
    ("Junior", re.compile(r"\b(?:junior|jr\.?|associate)\b", re.IGNORECASE)),
    ("Principal/Staff", re.compile(r"\b(?:principal|staff|distinguished)\b", re.IGNORECASE)),
    ("Head/Director", re.compile(r"\b(?:head of|director|vp|vice president|chief)\b", re.IGNORECASE)),
    ("Manager", re.compile(r"\bmanager\b", re.IGNORECASE)),
    ("Lead", re.compile(r"\blead\b", re.IGNORECASE)),
    ("Senior", re.compile(r"\b(?:senior|sr\.?)\b", re.IGNORECASE)),
]

# Phrases that contain UK place names but aren't in the UK. Removed before checking.
NON_UK_PHRASES = re.compile(
    r"new south wales|new england|london,?\s*(?:ontario|on\b|canada)"
    r"|cambridge,?\s*(?:ma\b|massachusetts)|birmingham,?\s*(?:al\b|alabama)"
    r"|manchester,?\s*(?:nh\b|new hampshire)|bristol,?\s*(?:ct\b|connecticut|tn\b|va\b)"
    r"|perth,?\s*(?:wa\b|australia)|newcastle,?\s*(?:nsw|australia)",
    re.IGNORECASE,
)
UK_PATTERN = re.compile(
    r"\b(?:uk|u\.k\.|united kingdom|great britain|england|scotland|wales|northern ireland"
    r"|london|manchester|edinburgh|glasgow|bristol|cambridge|oxford|leeds|birmingham"
    r"|belfast|cardiff|newcastle|sheffield|nottingham|liverpool|brighton|reading)\b",
    re.IGNORECASE,
)


def load_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    query = "SELECT board_id, title, location, departments, offices, content FROM jobs"
    return conn.execute(query).fetchall()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in items if item]


def clean_description(content: str | None) -> str:
    if not content:
        return ""
    return BeautifulSoup(html.unescape(content), "html.parser").get_text(" ", strip=True)


# Jobs per company
def jobs_per_company(jobs: list) -> Counter:
    return Counter(job["board_id"] for job in jobs)


# Department breakdown (a job in two departments counts towards both)
def department_breakdown(jobs: list) -> Counter:
    counts = Counter()
    for job in jobs:
        departments = _json_list(job["departments"]) or ["(none)"]
        counts.update(departments)
    return counts


# Skill leaderboard
def skill_leaderboard(jobs: list) -> list[tuple[str, int, float]]:
    texts = [f"{job['title'] or ''} {clean_description(job['content'])}" for job in jobs]
    results = []
    for skill, pattern in SKILLS.items():
        count = sum(1 for text in texts if pattern.search(text))
        results.append((skill, count, 100 * count / len(jobs) if jobs else 0.0))
    return sorted(results, key=lambda r: r[1], reverse=True)


# Seniority mix, from job titles
def seniority_of(title: str | None) -> str:
    for level, pattern in SENIORITY_LEVELS:
        if title and pattern.search(title):
            return level
    return "Unspecified"


def seniority_mix(jobs: list) -> Counter:
    return Counter(seniority_of(job["title"]) for job in jobs)


# Locations
def is_uk(job) -> bool:
    text = " ".join([job["location"] or "", *_json_list(job["offices"])])
    text = NON_UK_PHRASES.sub(" ", text)
    return bool(UK_PATTERN.search(text))


def location_summary(jobs: list) -> tuple[Counter, int]:
    locations = Counter((job["location"] or "(none)").strip() for job in jobs)
    uk_count = sum(1 for job in jobs if is_uk(job))
    return locations, uk_count


def _counter_lines(counter: Counter, total: int, top: int = TOP_N) -> list[str]:
    lines = []
    for name, count in counter.most_common(top):
        lines.append(f"  {name:<40} {count:>6}  ({100 * count / total:5.1f}%)")
    return lines


def build_report(jobs: list) -> list[str]:
    total = len(jobs)
    lines = [f"Analysis of {total} jobs, {datetime.now():%Y-%m-%d %H:%M}", ""]

    lines.append(f"1. Jobs per company (top {TOP_N})")
    lines += _counter_lines(jobs_per_company(jobs), total)

    lines += ["", f"2. Departments (top {TOP_N})"]
    lines += _counter_lines(department_breakdown(jobs), total)

    lines += ["", "3. Skills mentioned (share of all jobs)"]
    for skill, count, pct in skill_leaderboard(jobs):
        lines.append(f"  {skill:<40} {count:>6}  ({pct:5.1f}%)")

    lines += ["", "4. Seniority (from job titles)"]
    lines += _counter_lines(seniority_mix(jobs), total, top=len(SENIORITY_LEVELS) + 1)

    locations, uk_count = location_summary(jobs)
    lines += ["", f"5. Locations (top {TOP_N})"]
    lines += _counter_lines(locations, total)
    lines.append(f"  UK-related jobs: {uk_count} of {total} ({100 * uk_count / total:.1f}%)" if total else "")

    return lines


def main() -> None:
    conn = db.connect()
    jobs = load_jobs(conn)
    conn.close()

    if not jobs:
        print("No jobs in the database yet.")
        return

    lines = build_report(jobs)
    report = "\n".join(lines)
    print(report)
    REPORT_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"\nSaved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
