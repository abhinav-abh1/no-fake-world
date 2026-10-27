from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Source
from app.db.session import SessionLocal

LICENSE_NOTE = "Headlines and short snippets with a link back. Terms not yet reviewed."

# Starting list. Feeds move or disappear, so run check_feeds after any change.
# lean_hint is left empty on purpose: we fill it later from public ratings (Phase 9).
SEED_SOURCES: list[dict[str, str]] = [
    {
        "name": "BBC News - World",
        "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "homepage_url": "https://www.bbc.com/news/world",
        "country": "GB",
        "language": "en",
    },
    {
        "name": "Al Jazeera - All",
        "feed_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "homepage_url": "https://www.aljazeera.com",
        "country": "QA",
        "language": "en",
    },
    {
        "name": "DW - Top stories",
        "feed_url": "https://rss.dw.com/rdf/rss-en-all",
        "homepage_url": "https://www.dw.com/en",
        "country": "DE",
        "language": "en",
    },
    {
        "name": "The Guardian - World",
        "feed_url": "https://www.theguardian.com/world/rss",
        "homepage_url": "https://www.theguardian.com/world",
        "country": "GB",
        "language": "en",
    },
    {
        "name": "NPR - World",
        "feed_url": "https://feeds.npr.org/1004/rss.xml",
        "homepage_url": "https://www.npr.org/sections/world/",
        "country": "US",
        "language": "en",
    },
    {
        "name": "France 24 - English",
        "feed_url": "https://www.france24.com/en/rss",
        "homepage_url": "https://www.france24.com/en/",
        "country": "FR",
        "language": "en",
    },
    {
        "name": "Sky News - World",
        "feed_url": "https://feeds.skynews.com/feeds/rss/world.xml",
        "homepage_url": "https://news.sky.com/world",
        "country": "GB",
        "language": "en",
    },
    {
        "name": "The Hindu - International",
        "feed_url": "https://www.thehindu.com/news/international/feeder/default.rss",
        "homepage_url": "https://www.thehindu.com/news/international/",
        "country": "IN",
        "language": "en",
    },
]


def seed(db: Session) -> int:
    """Insert missing sources. Safe to run many times. Returns how many were added."""
    existing = set(db.scalars(select(Source.feed_url)))
    added = 0
    for row in SEED_SOURCES:
        if row["feed_url"] in existing:
            continue
        db.add(Source(**row, license_notes=LICENSE_NOTE))
        added += 1
    db.commit()
    return added


def main() -> None:
    with SessionLocal() as db:
        print(f"added {seed(db)} sources")


if __name__ == "__main__":
    main()
