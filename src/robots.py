from urllib import robotparser as rbp
from urllib.parse import urlparse
import httpx

DEFAULT_CRAWL_DELAY = 1.5
MAX_CRAWL_DELAY = 30.0

class RobotsChecker:
    def __init__(self, client: httpx.Client, agent_name: str):
        self.agent_name = agent_name
        self._client = client
        self._rules = {}

    def _link_to_host(self, link: str) -> str:
        link = link.strip()
        if not urlparse(link).scheme:
            link = "https://" + link
        parsed_link = urlparse(link)
        return f"{parsed_link.scheme}://{parsed_link.netloc.lower()}"

    def _parse_rules(self, link: str) -> None:
        host = self._link_to_host(link)
        robots_link = f"{host}/robots.txt"

        parser = rbp.RobotFileParser()

        try:
            response = self._client.get(robots_link)
        except httpx.RequestError:
            parser.parse(["User-agent: *", "Disallow: /"])
        else:
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
                delay = parser.crawl_delay(self.agent_name)
                if delay is not None and delay > MAX_CRAWL_DELAY:
                    print(f"Skipping {host}: crawl delay of {delay}s exceeds {MAX_CRAWL_DELAY}s")
                    parser = rbp.RobotFileParser()
                    parser.parse(["User-agent: *", "Disallow: /"])
            elif response.status_code in (401, 403):
                parser.parse(["User-agent: *", "Disallow: /"])
            elif response.status_code < 500:
                parser.parse([])
            else:
                parser.parse(["User-agent: *", "Disallow: /"])

        self._rules[host] = parser

    def check_rule(self, link: str) -> bool:
        host = self._link_to_host(link)
        if host not in self._rules:
            self._parse_rules(link)

        return self._rules[host].can_fetch(self.agent_name, link)

    def crawl_delay(self, link:str) -> float:
        host = self._link_to_host(link)
        if host not in self._rules:
            self._parse_rules(link)

        delay = self._rules[host].crawl_delay(self.agent_name)
        if delay is None:
            return DEFAULT_CRAWL_DELAY
        elif delay < DEFAULT_CRAWL_DELAY:
            delay = DEFAULT_CRAWL_DELAY
        return delay
