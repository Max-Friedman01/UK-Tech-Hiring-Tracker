import httpx

HEADERS = {
    "User-Agent": "ScraperProject/0.1 (https://github.com/Max-Friedman01/scraper_project; maxfriedo@outlook.com)"
}

def fetch(url: str) -> str | None:
    try:
        response = httpx.get(url, timeout=10.0, headers=HEADERS)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        print(f"Error, status: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Error, no response: {e}")
    return None