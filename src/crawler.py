import httpx
from bs4 import BeautifulSoup
import json
from pathlib import Path
from robots import RobotsChecker
from fetch import fetch, make_client
from urllib.parse import urljoin, urldefrag, urlparse
from urls import link_to_host
import tldextract
import time
import re

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

GREENHOUSE_FORMATS = [
    re.compile(r"greenhouse\.io/embed/[a-z_/]+\?(?:[^#\s]*&)?for=([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"boards-api(?:\.eu)?\.greenhouse\.io/v1/boards/([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"^https?://(?:job-)?boards(?:\.eu)?\.greenhouse\.io/(?!embed\b)([a-z0-9_-]+)", re.IGNORECASE)
]

MAX_PAGES_PER_SITE = 15
MAX_DEPTH_PER_SITE = 3

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
            return crawl_careers(client, response, link)
    return None

def crawl_header_footer(client: httpx.Client, response: httpx.Response, base_url: str) -> str | None:
    return None

def crawl_careers(client: httpx.Client, response: httpx.Response) -> str | None:
    if not is_html(response):
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    base_url = str(response.url)
    url_list = urls_from_html(soup, base_url)


def urls_from_html(soup: BeautifulSoup, base_url: str) -> list[str]:
    urls = []
    for element in soup.select("a[href], iframe[src], script[src]"):
        raw = (element.get("href") or element.get("src") or "").strip()
        if not raw:
            continue
        full = urldefrag(urljoin(base_url, raw)).url
        if urlparse(full).scheme not in ("http", "https"):
            continue
        urls.append(full)
    return list(dict.fromkeys(urls))

def look_for_greenhouse(urls: list[str]) -> str | None:
    for url in urls:
        for gh_format in GREENHOUSE_FORMATS:
            match = gh_format.search(url)
            if match:
                return match.group(1).lower()
    return None


def is_html(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return False
    return True