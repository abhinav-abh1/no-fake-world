import html
import re
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Article, RunLog, Source

MAX_ENTRIES_PER_FEED = 200
TITLE_MAX_CHARS = 500
SNIPPET_MAX_CHARS = 500  # we keep a short snippet and a link, never the full article
TRACKING_PARAMS = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "ocid", "cmpid", "ref", "ref_src",
    "at_medium", "at_campaign",
}  # fmt: skip
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def canonicalize_url(url: str) -> str:
    """Lowercase the host, drop #fragments and tracking parameters."""
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), "")
    )


def clean_text(raw: str | None, limit: int) -> str | None:
    """Remove HTML tags, decode entities, squeeze spaces, cut to `limit` characters."""
    if not raw:
        return None
    text = html.unescape(_TAG_RE.sub(" ", raw))
    text = _SPACE_RE.sub(" ", text).strip()
    return text[:limit] if text else None


def _published(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    year, month, day, hour, minute, second = parsed[:6]  # feedparser gives UTC time
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def parse_feed(content: bytes, source_id: uuid.UUID, language: str | None) -> list[dict[str, Any]]:
    """Turn raw feed bytes into article rows. Pure function: no network, no database."""
    rows: dict[str, dict[str, Any]] = {}  # keyed by url, so repeats inside a feed collapse
    for entry in feedparser.parse(content).entries[:MAX_ENTRIES_PER_FEED]:
        link = entry.get("link") or ""
        title = clean_text(entry.get("title"), TITLE_MAX_CHARS)
        if not title or not link.startswith(("http://", "https://")):
            continue  # unusable entry, or a link we don't want (javascript:, mailto:, ...)
        url = canonicalize_url(link)
        rows.setdefault(
            url,
            {
                "id": uuid.uuid4(),
                "source_id": source_id,
                "url": url,
                "title": title,
                "snippet": clean_text(
                    entry.get("summary") or entry.get("description"), SNIPPET_MAX_CHARS
                ),
                "language": language,
                "published_at": _published(entry),
            },
        )
    return list(rows.values())


def save_articles(db: Session, rows: list[dict[str, Any]]) -> int:
    """Insert new articles. Rows whose url already exists are silently skipped."""
    if not rows:
        return 0
    stmt = (
        insert(Article)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["url"])
        .returning(Article.id)
    )
    return len(db.execute(stmt).all())


def collect_source(db: Session, client: httpx.Client, source: Source) -> tuple[int, int]:
    """Fetch one feed. Returns (entries seen, new articles saved)."""
    response = client.get(source.feed_url)
    response.raise_for_status()
    rows = parse_feed(response.content, source.id, source.language)
    saved = save_articles(db, rows)
    db.commit()
    return len(rows), saved


def run_collection(db: Session, client: httpx.Client) -> RunLog:
    """Collect every active source. One failing source never stops the others."""
    run = RunLog(job_name="collect_rss", status="running")
    db.add(run)
    db.commit()

    sources = list(db.scalars(select(Source).where(Source.is_active).order_by(Source.name)))
    seen = saved = 0
    errors: list[dict[str, str]] = []
    for source in sources:
        name = source.name  # read before any rollback can expire the object
        try:
            n_seen, n_saved = collect_source(db, client, source)
        except (httpx.HTTPError, SQLAlchemyError) as exc:
            db.rollback()
            errors.append({"source": name, "error": f"{type(exc).__name__}: {exc}"[:300]})
            continue
        seen += n_seen
        saved += n_saved

    run.finished_at = datetime.now(UTC)
    run.items_in = seen
    run.items_out = saved
    run.errors = errors or None
    if not errors:
        run.status = "ok"
    elif len(errors) == len(sources):
        run.status = "failed"
    else:
        run.status = "partial"
    db.commit()
    return run
