from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

ROBOTS_TOKEN = "NoFakeWorldBot"  # the name sites see in robots.txt rules


class RobotsCache:
    """Reads each site's robots.txt once and answers: may we fetch this URL?"""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._rules: dict[str, RobotFileParser | bool] = {}  # True = allow all, False = deny all

    def _load(self, origin: str) -> RobotFileParser | bool:
        try:
            response = self._client.get(f"{origin}/robots.txt")
        except httpx.HTTPError:
            return False  # cannot read the rules: be careful and stay away
        if response.status_code == 200:
            parser = RobotFileParser()
            parser.parse(response.text.splitlines())
            return parser
        if 400 <= response.status_code < 500:
            return True  # no robots.txt published: nothing is forbidden
        return False  # server error: stay away

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._rules:
            self._rules[origin] = self._load(origin)
        rules = self._rules[origin]
        if isinstance(rules, bool):
            return rules
        return rules.can_fetch(ROBOTS_TOKEN, url)
