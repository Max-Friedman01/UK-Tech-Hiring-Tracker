import db
from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RECORD_WORD_FREQUENCY_PATH = DATA_DIR / "inputted_word_frequencies.jsonl"

def record_word_frequency() -> None:
    word = input("Input term here:").lower()
    conn = db.connect()
    no_jobs = db.count_jobs(conn)
    jobs = db.load_job_texts(conn)
    conn.close()
    jobs_with_word = 0
    for job in jobs:
        job_has_word = False
        for feature in job:
            if feature is None:
                continue
            if word in feature.lower():
                jobs_with_word += 1
                job_has_word = True
                break
            if job_has_word:
                break

    save_string(f"{word}: {jobs_with_word}/{no_jobs}", Path(RECORD_WORD_FREQUENCY_PATH))

def save_string(line: str, path: Path) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

if __name__ == "__main__":
    record_word_frequency()