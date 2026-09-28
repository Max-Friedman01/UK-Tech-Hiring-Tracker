from models import Job
from fetch import make_client, FetchError
from sources import greenhouse as gh
import time

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