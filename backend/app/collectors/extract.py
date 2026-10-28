import hashlib
import time
from datetime import UTC, datetime

import httpx
import trafilatura
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.collectors.robots import RobotsCache
from app.db.models import Article, RunLog, Source

MIN_TEXT_CHARS = 200  # shorter than this is probably a menu, a paywall or an error page
MAX_TEXT_CHARS = 60_000
MAX_PAGE_BYTES = 2_000_000


def extract_text(page_html: str) -> str | None:
    """Main article text, or None if nothing convincing was found."""
    text = trafilatura.extract(
        page_html,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not text or len(text) < MIN_TEXT_CHARS:
        return None
    return str(text)[:MAX_TEXT_CHARS]


def text_hash(text: str) -> str:
    """Fingerprint of the text, ignoring case and spacing. Used for duplicate detection later."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def fetch_page(client: httpx.Client, url: str) -> str | None:
    response = client.get(url)
    response.raise_for_status()
    if "html" not in response.headers.get("content-type", "").lower():
        return None
    if len(response.content) > MAX_PAGE_BYTES:
        return None
    return response.text


def _process_one(client: httpx.Client, robots: RobotsCache, article: Article) -> str:
    """Returns the article's new status. May raise httpx.HTTPError."""
    if not robots.allowed(article.url):
        return "skipped_robots"
    page = fetch_page(client, article.url)
    text = extract_text(page) if page else None
    if text is None:
        return "failed"
    article.body_text = text
    article.content_hash = text_hash(text)
    return "extracted"


def extract_pending(
    db: Session, client: httpx.Client, limit: int = 50, delay: float = 1.0
) -> RunLog:
    """Extract text for the newest unprocessed articles of sources we are allowed to fetch."""
    run = RunLog(job_name="extract_text", status="running")
    db.add(run)
    db.commit()

    stmt = (
        select(Article)
        .join(Source, Source.id == Article.source_id)
        .where(
            Article.status == "fetched",
            Article.body_text.is_(None),
            Source.robots_ok.is_(True),
            Source.is_active.is_(True),
        )
        .order_by(Article.published_at.desc().nulls_last())
        .limit(limit)
    )
    articles = list(db.scalars(stmt))
    robots = RobotsCache(client)
    counts = {"extracted": 0, "failed": 0, "skipped_robots": 0}
    errors: list[dict[str, str]] = []

    for article in articles:
        url = article.url
        try:
            status = _process_one(client, robots, article)
        except httpx.HTTPError as exc:
            status = "failed"
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"[:300]})
        article.status = status
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            errors.append({"url": url, "error": f"{type(exc).__name__}"})
            continue
        counts[status] += 1
        if status != "skipped_robots":
            time.sleep(delay)  # be gentle: one request at a time, with a pause

    run.finished_at = datetime.now(UTC)
    run.items_in = len(articles)
    run.items_out = counts["extracted"]
    run.errors = errors or None
    run.status = "ok" if not errors else "partial"
    db.commit()
    return run
