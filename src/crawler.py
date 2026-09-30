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
import copy
from sources import greenhouse

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
    re.compile(r"(?:job-)?boards(?:\.eu)?\.greenhouse\.io/embed/[a-z_/]+\?(?:[^#\s]*&)?for=([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"boards-api(?:\.eu)?\.greenhouse\.io/v1/boards/([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"^https?://(?:job-)?boards(?:\.eu)?\.greenhouse\.io/(?!embed\b)([a-z0-9_-]+)", re.IGNORECASE),
]

GREENHOUSE_TEXT_FORMATS = [
    re.compile(r"(?:job-)?boards(?:\.eu)?\.greenhouse\.io\\?/embed\\?/[a-z_\\/]+\?(?:[^#\s\"']*&)?for=([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"boards-api(?:\.eu)?\.greenhouse\.io\\?/v1\\?/boards\\?/([a-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"https?:\\?/\\?/(?:job-)?boards(?:\.eu)?\.greenhouse\.io\\?/(?!embed\b)([a-z0-9_-]+)", re.IGNORECASE),
]

FILE_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip",
                   ".doc", ".docx", ".mp4", ".css", ".js")

MAX_PAGES_PER_SITE = 30
MAX_DEPTH_PER_SITE = 3

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RESULTS_PATH = DATA_DIR / "crawl_results.jsonl"

def get_companies(path: Path = DATA_DIR / "wikidata_companies.json") -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)

def crawl_company(client: httpx.Client, robot: RobotsChecker, company: dict) -> dict:
    link = link_to_host(company["website"])
    board = None
    num_pages = 0
    visited_pages = []
    for suffix in SUFFIXES:
        try_link = urljoin(link, suffix)
        board, num_pages, visited_pages = attempt_link(client, try_link, robot, num_pages, visited_pages)
        if board is not None:
            break
        if num_pages >= MAX_PAGES_PER_SITE:
            print(f"{num_pages} visited")
            return {**company, "board_id": None, "status": "not found"}
    if board is None:
        num_pages -= 5
        parts = tldextract.extract(link)
        for prefix in PREFIXES:
            try_link = f"https://{prefix}.{parts.domain}.{parts.suffix}"
            board, num_pages, visited_pages = attempt_link(client, try_link, robot, num_pages, visited_pages)
            if board is not None:
                break
            if num_pages >= MAX_PAGES_PER_SITE:
                print(f"{num_pages} visited")
                return {**company, "board_id": None, "status": "not found"}
    if board is None:
        print(f"{num_pages} visited")
        return {**company, "board_id": None, "status": "not found"}
    print(f"{num_pages} visited")
    return {**company, "board_id": board, "status": "found"}

def attempt_link(client: httpx.Client,
                 link: str,
                 robot: RobotsChecker,
                 num_pages: int,
                 visited_pages: list[str]
                 ) -> tuple[str | None, int, list[str]]:
    if robot.check_rule(link):
        response = fetch(client, link)
        num_pages += 1
        visited_pages.append(link)
        delay = robot.crawl_delay(link)
        time.sleep(delay)
        if response is not None:
            visited_pages.append(str(response.url))
            return crawl_careers(client, response, robot, link, num_pages, visited_pages)
    return None, num_pages, list(set(visited_pages))

def crawl_header_footer(client: httpx.Client, response: httpx.Response, base_url: str) -> str | None:
    return None

def crawl_careers(client: httpx.Client,
                  response: httpx.Response,
                  robot: RobotsChecker,
                  first_url: str,
                  num_pages: int,
                  visited_pages: list[str]
                  ) -> tuple[str | None, int, list[str]]:
    visited_pages.extend([first_url, str(response.url)])
    if not is_html(response):
        return None, num_pages, list(set(visited_pages))
    soup = BeautifulSoup(response.text, "html.parser")
    url_list = urls_from_html(main_content(soup), str(response.url))
    board = look_for_greenhouse([str(response.url), *url_list])
    if board is not None:
        return board, num_pages, list(set(visited_pages))
    board = greenhouse_from_text(response.text)
    if board is not None:
            return board, num_pages, list(set(visited_pages))
    for _ in range(0, MAX_DEPTH_PER_SITE):
        url_list, num_pages, visited_pages, board = crawl_next_pages(url_list,
                                                              urlparse(str(response.url)).hostname,
                                                              robot,
                                                              client,
                                                              num_pages,
                                                              visited_pages)
        if board is not None:
            return board, num_pages, list(set(visited_pages))
        board = look_for_greenhouse(url_list)
        if board is not None:
            return board, num_pages, list(set(visited_pages))
        if num_pages >= MAX_PAGES_PER_SITE:
            break
    return None, num_pages, list(set(visited_pages))

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

def main_content(soup: BeautifulSoup) -> BeautifulSoup:
    body = copy.copy(soup)

    main = body.select_one("main, [role='main']")
    if main is not None:
        return BeautifulSoup(str(main), "html.parser")

    for element in body.select("header, nav, footer, [role='banner'], [role='navigation'], [role='contentinfo']"):
        element.decompose()
    return body

def look_for_greenhouse(urls: list[str]) -> str | None:
    for url in urls:
        for gh_format in GREENHOUSE_FORMATS:
            match = gh_format.search(url)
            if match:
                return match.group(1).lower()
    return None

def greenhouse_from_text(text:str) -> str | None:
    for gh_format in GREENHOUSE_TEXT_FORMATS:
        match = gh_format.search(text)
        if match is not None:
            return match.group(1).lower()
    return None

def crawl_next_pages(urls: list[str],
                     host_name: str,
                     robot: RobotsChecker,
                     client: httpx.Client,
                     num_pages: int,
                     visited_pages: list[str]
                     ) -> tuple[list[str], int, list[str], str | None]:
    compiled_urls = []
    for url in urls:
        if url in visited_pages:
            continue
        visited_pages.append(url)
        if num_pages >= MAX_PAGES_PER_SITE:
            return list(dict.fromkeys(compiled_urls)), num_pages, list(set(visited_pages)), None
        parsed_url = urlparse(url)
        if parsed_url.hostname != host_name:
            continue
        path = parsed_url.path.lower()
        if path.endswith(FILE_EXTENSIONS):
            continue
        delay = robot.crawl_delay(url)
        if not robot.check_rule(url):
            print(f"{url}: Blocked by robots.txt")
            continue
        response = fetch(client, url)
        time.sleep(delay)
        num_pages += 1
        if response is not None:
            if not is_html(response):
                    continue
            board = greenhouse_from_text(response.text)
            if board is not None:
                return list(dict.fromkeys(compiled_urls)), num_pages, list(set(visited_pages)), board
            visited_pages.append(str(response.url))
            soup = BeautifulSoup(response.text, "html.parser")
            soup_urls = urls_from_html(main_content(soup), str(response.url))
            compiled_urls.append(str(response.url))
            compiled_urls.extend(soup_urls)
    return list(dict.fromkeys(compiled_urls)), num_pages, list(set(visited_pages)), None

def is_html(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return False
    return True

def total_crawl() -> None:
    companies_with_boards = []
    companies = get_companies()
    num_companies = len(companies)
    done = load_done()
    with make_client() as client:
        robot = RobotsChecker(client, "ScraperProject")
        for i, company in enumerate(companies):
            if company["qid"] in done:
                continue
            try:
                dict_with_board = crawl_company(client, robot, company)
            except Exception as e:
                print(f"Error {e} for company {i+1}.")
                dict_with_board = {**company, "board_id": None, "status": "Site error", "error": f"{type(e).__name__}: {e}"}
            companies_with_boards.append(dict_with_board)
            save_result(dict_with_board)
            if dict_with_board["status"] == "found":
                print(f"Company {dict_with_board["name"]}, {i+1}/{num_companies} finished. Board found successfully - {dict_with_board["board_id"]}.")
            else:
                print(f"Company {dict_with_board["name"]}, {i+1}/{num_companies} finished. Board not found.")

def save_result(result: dict, path: Path = RESULTS_PATH) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

def load_done(path: Path = RESULTS_PATH) -> set[str]:
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {json.loads(line)["qid"] for line in lines if line.strip()}


KNOWN_GREENHOUSE = [
    {"name": "Monzo",      "website": "https://monzo.com",           "expected": "monzo"},
    {"name": "GoCardless", "website": "https://gocardless.com/",     "expected": "gocardless"},
    {"name": "Deliveroo",  "website": "https://deliveroo.co.uk/",    "expected": "deliveroo"},
    {"name": "Anthropic",  "website": "https://www.anthropic.com",   "expected": "anthropic"},
    {"name": "Figma",      "website": "https://www.figma.com",       "expected": "figma"},
    {"name": "Databricks", "website": "https://www.databricks.com",  "expected": "databricks"},
    {"name": "Stripe",     "website": "https://stripe.com",          "expected": "stripe"},
    {"name": "Canonical",  "website": "https://canonical.com",       "expected": "canonical"},
    {"name": "Cloud9",   "website": "http://www.cloud9mobile.co.uk", "expected": "wirelesslogic"},
    {"name": "Dwelly",   "website": "https://www.dwelly.group/",     "expected": "dwelly"},
    {"name": "Fideres",  "website": "http://fideres.com/",           "expected": "fideres"},
    {"name": "joblogic", "website": "https://www.joblogic.com",      "expected": "joblogic"},
]


def test_known(companies: list[dict] = KNOWN_GREENHOUSE) -> list[dict]:
    results = []
    with make_client() as client:
        robot = RobotsChecker(client, "ScraperProject")
        for i, company in enumerate(companies, start=1):
            expected = company["expected"]

            if greenhouse.check_board(client, expected) is None:
                print(f"[{i}/{len(companies)}] {company['name']}: expected board '{expected}' "
                      f"doesn't exist on Greenhouse, skipping")
                continue

            try:
                result = crawl_company(client, robot, company)
            except Exception as e:
                result = {**company, "board_id": None, "status": f"error: {type(e).__name__}: {e}"}

            found = result["board_id"]
            if found == expected:
                verdict = "CORRECT"
            elif found is None:
                verdict = "MISSED"
            else:
                verdict = f"WRONG (found '{found}')"

            print(f"[{i}/{len(companies)}] {company['name']}: {verdict}  status={result['status']}")
            results.append(result)

    correct = sum(r["board_id"] == r["expected"] for r in results)
    print(f"\n{correct}/{len(results)} known boards found correctly")
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_known()
    else:
        total_crawl()