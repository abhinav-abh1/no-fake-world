import feedparser
import httpx
from sqlalchemy import select

from app.collectors.http import make_client
from app.db.models import Source
from app.db.session import SessionLocal


def check_one(client: httpx.Client, url: str) -> str:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"FAIL   {type(exc).__name__}: {exc}"
    parsed = feedparser.parse(response.content)
    count = len(parsed.entries)
    if count == 0:
        return (
            f"EMPTY  http {response.status_code}, no entries (parse problem: {bool(parsed.bozo)})"
        )
    return f"OK     {count} entries"


def main() -> None:
    with SessionLocal() as db:
        sources = list(db.scalars(select(Source).where(Source.is_active).order_by(Source.name)))
    with make_client() as client:
        for source in sources:
            print(f"{source.name:<30} {check_one(client, source.feed_url)}")


if __name__ == "__main__":
    main()
