from pathlib import Path
import httpx
from fetch import fetch, make_client
import time
from datetime import datetime

GREENHOUSE_HOSTS = [
    "https://boards-api.greenhouse.io",
    "https://boards-api.eu.greenhouse.io",
]

def load_seed_boards(path: str = "data/board_ids.txt") -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

def check_host(client: httpx.Client, board_id: str) -> dict | None:
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

def discover() -> list[dict]:
    board_ids = sorted(set(load_seed_boards()))
    with make_client() as client:
        #return [record for board_id in board_ids if (record := check_host(client, board_id)) is not None]
        record_list = []
        for board_id in board_ids:
            record = check_host(client, board_id)
            if record is not None:
                record_list.append(record)
            else:
                print(f"{board_id} not found")
            time.sleep(0.5)
    return record_list