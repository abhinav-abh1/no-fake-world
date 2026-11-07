import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import Article, RunLog
from app.dedup.pairs import find_pairs


@dataclass(frozen=True)
class DedupResult:
    exact: int
    near: int


def _when(article: Article) -> datetime:
    return article.published_at or article.fetched_at


def _order_key(article: Article) -> tuple[datetime, str]:
    """Which article came first. The earliest is the original, later ones are copies."""
    return (_when(article), str(article.id))


def mark_duplicates(
    db: Session,
    model_name: str,
    min_cosine: float,
    min_jaccard: float,
    per_article: int = 5,
    same_outlet_minutes: float = 30.0,
    cross_outlet_hours: float = 6.0,
) -> DedupResult:
    """Recompute `is_duplicate_of_id` from scratch. Same data and thresholds, same answer.

    Near copies must also be close in time: one outlet listing a page twice does it within
    minutes, other outlets may reprint it hours later. A later, different page that reuses an
    opening sentence (a live blog, then the results page) is not a copy.
    """
    run = RunLog(job_name="mark_duplicates", status="running")
    db.add(run)
    db.execute(update(Article).values(is_duplicate_of_id=None))
    parent: dict[uuid.UUID, uuid.UUID] = {}  # copy id -> the earlier article it copies

    # 1) Exact copies: identical extracted text.
    repeated = (
        select(Article.content_hash)
        .where(Article.content_hash.is_not(None))
        .group_by(Article.content_hash)
        .having(func.count() > 1)
    )
    for content_hash in db.scalars(repeated):
        members = sorted(
            db.scalars(select(Article).where(Article.content_hash == content_hash)),
            key=_order_key,
        )
        for member in members[1:]:
            parent[member.id] = members[0].id
    exact = len(parent)

    # 2) Near copies: very close in meaning, sharing most exact wording, and close in time.
    for pair in find_pairs(db, model_name, min_cosine, per_article):
        if pair.jaccard < min_jaccard:
            continue
        older, newer = sorted((pair.a, pair.b), key=_order_key)
        gap_minutes = (_when(newer) - _when(older)).total_seconds() / 60
        same_outlet = older.source_id == newer.source_id
        allowed = same_outlet_minutes if same_outlet else cross_outlet_hours * 60
        if gap_minutes > allowed:
            continue
        parent.setdefault(newer.id, older.id)

    def root(article_id: uuid.UUID) -> uuid.UUID:
        while article_id in parent:  # every link points to an earlier article, so no loops
            article_id = parent[article_id]
        return article_id

    for child_id in parent:
        db.execute(
            update(Article).where(Article.id == child_id).values(is_duplicate_of_id=root(child_id))
        )

    run.finished_at = datetime.now(UTC)
    run.items_out = len(parent)
    run.status = "ok"
    db.commit()
    return DedupResult(exact=exact, near=len(parent) - exact)
