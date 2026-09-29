import httpx
from bs4 import BeautifulSoup
import json
from dataclasses import asdict
from pathlib import Path

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