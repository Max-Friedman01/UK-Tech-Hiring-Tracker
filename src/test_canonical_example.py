from bs4 import BeautifulSoup
from fetch import make_client, fetch
from robots import RobotsChecker
from crawler import urls_from_html, main_content, look_for_greenhouse, is_html

url = "https://canonical.com/careers"
with make_client() as client:
    robot = RobotsChecker(client, "ScraperProject")
    print("robots allows:", robot.check_rule(url))

    response = fetch(client, url)
    print("response:", None if response is None else (response.status_code, str(response.url)))
    if response is not None:
        print("is_html:", is_html(response))
        print("'greenhouse' in raw HTML:", response.text.lower().count("greenhouse"))

        soup = BeautifulSoup(response.text, "html.parser")
        all_urls = urls_from_html(soup, str(response.url))
        main_urls = urls_from_html(main_content(soup), str(response.url))
        gh_all = [u for u in all_urls if "greenhouse" in u.lower()]
        gh_main = [u for u in main_urls if "greenhouse" in u.lower()]
        print("greenhouse URLs, whole page:", len(gh_all), gh_all[:5])
        print("greenhouse URLs, main content:", len(gh_main), gh_main[:5])
        print("board found:", look_for_greenhouse(gh_all))