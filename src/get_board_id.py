import httpx
from bs4 import BeautifulSoup

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