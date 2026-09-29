import httpx
from bs4 import BeautifulSoup
import json
from dataclasses import asdict
from pathlib import Path
from robots import RobotsChecker
from fetch import fetch, make_client
from urllib.parse import urljoin, urldefrag
from urls import link_to_host
import tldextract
import time

SUFFIXES = [
    "/careers",
    "/jobs",
    "/join-us",
    "/work-with-us",
    "/about/careers",
    "/company/careers",
    "/careers/jobs",
    "/join",
    "/work-for-us",
    "/opportunities",
    "/vacancies",
    "/open-positions",
    "/hiring",
    "/about-us/careers",
    "/en/careers",
    "/en-gb/careers",
    "/gb/careers",
    "/uk/careers"
]

PREFIXES = [
    "careers",
    "jobs",
    "work"
]

def get_companies(path: str = "data/wikidata_companies.json") -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)

def crawl_company(client: httpx.Client, robot: RobotsChecker, company: dict) -> dict:
    link = link_to_host(company["website"])
    board = None
    for suffix in SUFFIXES:
        try_link = urljoin(link, suffix)
        board = attempt_link(client, try_link, robot)
        if board is not None:
            break
    if board is None:
        parts = tldextract.extract(link)
        for prefix in PREFIXES:
            try_link = f"https://{prefix}.{parts.domain}.{parts.suffix}"
            board = attempt_link(client, try_link, robot)
            if board is not None:
                break
    if board is None:
        return {**company, "board_id": None, "status": "not found"}
    return {**company, "board_id": board, "status": "found"}

def attempt_link(client: httpx.Client, link: str, robot: RobotsChecker) -> str | None:
    delay = robot.crawl_delay(link)
    if robot.check_rule(link):
        response = fetch(client, link)
        time.sleep(delay)
        if response is not None:
            return crawl_careers(client, response)
    return None

def crawl_careers(client: httpx.Client, response: httpx.Response) -> str | None:
    if not is_html(response):
        return None
    return None

def is_html(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return False
    return True