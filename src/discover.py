from pathlib import Path
from fetch import make_client
import time
from sources.greenhouse import check_board
import json





def load_seed_boards(path: str = "data/board_ids.txt") -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

def discover() -> list[dict]:
    board_ids = sorted(set(load_seed_boards()))
    with make_client() as client:
        record_list = []
        for board_id in board_ids:
            record = check_board(client, board_id)
            if record is not None:
                record_list.append(record)
            else:
                print(f"{board_id} not found")
            time.sleep(0.5)
    return record_list

def save_boards(boards: list[dict], path: str = "data/boards.json") -> None:
    text = json.dumps(boards, indent=2)
    Path(path).write_text(text, encoding="utf-8")

if __name__ == "__main__":
    boards = discover()
    save_boards(boards)