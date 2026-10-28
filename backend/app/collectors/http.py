import httpx

# Honest identification: sites can see who is fetching and how to reach us.
USER_AGENT = "NoFakeWorldBot/0.1 (+https://github.com/abhinav-abh1/no-fake-world)"


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
        timeout=httpx.Timeout(15.0),
        follow_redirects=True,
        transport=transport,
    )
