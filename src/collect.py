from models import Job
from fetch import make_client, FetchError
from sources import greenhouse as gh
import time
from pathlib import Path
import json
from datetime import datetime
import db

def get_boards(path: str = "data/boards.json") -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)

def collect(boards: list[dict]) -> tuple[list[Job], list[dict]]:
    job_list = []
    failed_boards = []
    with make_client() as client:
        for board in boards:
            try:
                raw_jobs_list = gh.fetch_jobs(client, board)
                for raw_job in raw_jobs_list:
                    job_list.append(gh.parse_job(board, raw_job))
            except FetchError as e:
                print(f"Failed: {e}")
                failed_boards.append(board)
            time.sleep(0.5)
    return job_list, failed_boards

if __name__ == "__main__":
    seen_at = datetime.now().isoformat(timespec="seconds")
    boards = get_boards()
    jobs, failed_boards = collect(boards)

    conn = db.connect()
    save_jobs_count_before = db.count_jobs(conn)
    db.save_jobs(conn, jobs, seen_at)
    total = db.count_jobs(conn)
    conn.close()

    print(f"Collected {len(jobs)} jobs from {len(boards) - len(failed_boards)}/{len(boards)} boards")
    print(f"Database now holds {total} jobs ({total - save_jobs_count_before} new)")
    for board in failed_boards:
        print(f"  failed: {board['board_id']}")