import httpx
from bs4 import BeautifulSoup
import json
from dataclasses import asdict
from pathlib import Path
from robots import RobotsChecker
from fetch import fetch, make_client
from urllib.parse import urljoin, urldefrag

SUFFIXES = [
    "/careers"
    "/jobs"
    "/join-us"
    "/work-with-us"
    "/about/careers"
    "/company/careers"
    "/careers/jobs"
    "/join"
    "/work-for-us"
    "/opportunities"
    "/vacancies"
    "/open-positions"
    "/hiring"
    "/about-us/careers"
    "/en/careers"
    "/en-gb/careers"
    "/gb/careers"
    "/uk/careers"
]

PREFIXES = [
    "careers."
    "jobs."
    "work."
]

def get_companies(path: str = "data/wikidata_companies.json") -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)

def get_links(companies: list[dict]) -> list[str]:
    return [company["website"] for company in companies]

def crawler(links: list[str]) -> list[str]:
    with make_client() as client:
        robot = RobotsChecker(client, "Jobs Crawler")
        for link in links:
            hit = False
            for suffix in SUFFIXES:
                try_link = urljoin(link, suffix)
                if robot.check_rule(try_link):
                    response = fetch(try_link)
                    if response is not None:
                        hit = True
                        crawl_careers(client, try_link)
                        break
            if hit == False:
                for prefix in PREFIXES:
                    break
    return None

def crawl_careers(client: httpx.Client, link: str) -> None:
    return None