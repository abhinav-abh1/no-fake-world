import uuid

import httpx
from sqlalchemy import func, select

from app.collectors.http import make_client
from app.collectors.rss import canonicalize_url, parse_feed, run_collection
from app.db.models import Article, RunLog, Source
from app.db.session import SessionLocal

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test feed</title>
<item>
  <title>First &amp; story</title>
  <link>https://example.com/a?utm_source=x&amp;id=1#top</link>
  <description>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt;</description>
  <pubDate>Tue, 27 Oct 2026 10:00:00 GMT</pubDate>
</item>
<item>
  <title>Second story</title>
  <link>https://example.com/b</link>
  <description>Plain text</description>
</item>
<item><title>No link here</title><description>skipped</description></item>
</channel></rss>"""


def test_canonicalize_url_removes_tracking() -> None:
    url = "HTTPS://Example.com/a?utm_source=x&id=1&fbclid=z#frag"
    assert canonicalize_url(url) == "https://example.com/a?id=1"


def test_parse_feed_extracts_and_cleans() -> None:
    rows = parse_feed(SAMPLE_RSS, uuid.uuid4(), "en")
    assert [row["url"] for row in rows] == ["https://example.com/a?id=1", "https://example.com/b"]
    assert rows[0]["title"] == "First & story"
    assert rows[0]["snippet"] == "Hello world"
    assert rows[0]["published_at"].year == 2026
    assert rows[0]["published_at"].tzinfo is not None
    assert rows[1]["published_at"] is None


def _fake_internet(request: httpx.Request) -> httpx.Response:
    if "broken" in request.url.host:
        return httpx.Response(500)
    return httpx.Response(200, content=SAMPLE_RSS)


def test_collection_is_idempotent_and_logged() -> None:
    with SessionLocal() as db:
        db.add_all(
            [
                Source(name="Good", feed_url="https://good.example/rss", language="en"),
                Source(name="Broken", feed_url="https://broken.example/rss"),
            ]
        )
        db.commit()
        client = make_client(httpx.MockTransport(_fake_internet))

        first = run_collection(db, client)
        assert (first.items_in, first.items_out, first.status) == (2, 2, "partial")
        assert first.errors is not None
        assert first.errors[0]["source"] == "Broken"

        second = run_collection(db, client)
        assert second.items_out == 0  # nothing new the second time

        assert db.scalar(select(func.count()).select_from(Article)) == 2
        assert db.scalar(select(func.count()).select_from(RunLog)) == 2
