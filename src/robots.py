from urllib import robotparser as rbp
from urllib.parse import urlparse
import httpx

class RobotsChecker:
    def __init__(self, agent_name: str, client: httpx.Client):
        self.agent_name = agent_name
        self.client = client
        self._rules = {}

    def parse_rules(link: str) -> None:
        parsed_link = urlparse(link)
        robots_link = f"{parsed_link.scheme}://{(parsed_link.network).lower()}/robots.txt"
        
