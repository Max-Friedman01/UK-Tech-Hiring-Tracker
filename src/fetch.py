import httpx

HEADERS = {
    "User-Agent": "ScraperProject/0.1 (https://github.com/Max-Friedman01/scraper_project; maxfriedo@outlook.com)"
}

def make_client() -> httpx.Client:
    return httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True)

def fetch_non_client(url: str) -> httpx.Response | None:
    try:
        response = httpx.get(url, timeout=15.0, headers=HEADERS)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        print(f"Error, status: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Error, no response: {e}")
    return None

def fetch(client: httpx.Client, url: str) -> httpx.Response | None:
    try:
        response = client.get(url, timeout=15.0, headers=HEADERS)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        print(f"Error, status: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"Error, no response: {e}")
    return None