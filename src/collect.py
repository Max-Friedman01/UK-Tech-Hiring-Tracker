from models import Job
from fetch import make_client
from sources import greenhouse as gh
import time

def collect(boards: list[dict]) -> list[Job]:
    job_list = []
    with make_client() as client:
        for board in boards:
            raw_jobs_list = gh.fetch_jobs(client, board)
            for raw_job in raw_jobs_list:
                job_list.append(gh.parse_job(board, raw_job))
            time.sleep(0.5)
    return job_list