import httpx
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "ScraperProject/0.1 (https://github.com/Max-Friedman01/scraper_project; maxfriedo@outlook.com)"
}

site = "https://en.wikipedia.org/wiki/Forbes_list_of_the_most_valuable_football_clubs"

try:
    response = httpx.get(site, timeout=10.0, headers=headers)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    print(f"Error, status: {e.response.status_code}")
except httpx.HTTPRequestError as e:
    print("Error, No Response")

print("2026" in response.text)

soup = BeautifulSoup(response.text, "html.parser")