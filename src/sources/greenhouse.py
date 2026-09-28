import httpx
from fetch import fetch
import time
from models import Job
import json
from datetime import datetime

GREENHOUSE_HOSTS = [
    "https://boards-api.greenhouse.io",
    "https://boards-api.eu.greenhouse.io",
]

def jobs_url(board: dict) -> str:
    return f"{board["host"]}/v1/boards/{board["board_id"]}/jobs"

def fetch_jobs(client: httpx.Client, board: dict) -> list[dict]:
    response = fetch(client, jobs_url(board), params={"content": "true"})
    if response is None:
        return []
    return response.json().get("jobs", [])

def check_board(client: httpx.Client, board_id: str) -> dict | None:
    for host in GREENHOUSE_HOSTS:
        response = fetch(client, f"{host}/v1/boards/{board_id}")
        if response is not None:
            return {
                    "platform": "greenhouse",
                    "board_id": board_id,
                    "host": host,
                    "company": response.json().get("name"),
                    "discovered_at": datetime.now().isoformat(timespec="seconds")
                }
        time.sleep(0.5)
    return None

def parse_job(board: dict, raw_job: dict) -> Job:
    return Job(
        job_id=str(raw_job["id"]),
        platform="greenhouse",
        board_id=board["board_id"],
        title=raw_job.get("title", ""),
        location=(raw_job.get("location") or {}).get("name"),
        departments=[department.get("name") for department in raw_job.get("departments") or []],
        offices=[office.get("location") or office.get("name") for office in raw_job.get("offices") or []],
        url=raw_job.get("absolute_url"),
        updated_at=raw_job.get("updated_at"),
        first_published=raw_job.get("first_published"),
        content=raw_job.get("content"),
        raw_json=json.dumps(raw_job)
    )