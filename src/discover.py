from pathlib import Path
import httpx
from fetch import fetch, make_client
import time
from datetime import datetime
from sources.greenhouse import check_board

GREENHOUSE_HOSTS = [
    "https://boards-api.greenhouse.io",
    "https://boards-api.eu.greenhouse.io",
]

def load_seed_boards(path: str = "data/board_ids.txt") -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

def discover() -> list[dict]:
    board_ids = sorted(set(load_seed_boards()))
    with make_client() as client:
        #return [record for board_id in board_ids if (record := check_host(client, board_id)) is not None]
        record_list = []
        for board_id in board_ids:
            record = check_board(client, board_id)
            if record is not None:
                record_list.append(record)
            else:
                print(f"{board_id} not found")
            time.sleep(0.5)
    return record_list