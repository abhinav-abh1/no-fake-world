import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import Article, RunLog
from app.dedup.pairs import PairScore, find_pairs
from app.dedup.similarity import dedup_text, figures_conflict


@dataclass(frozen=True)
class DedupResult:
    exact: int
    near: int


def _when(article: Article) -> datetime:
    return article.published_at or article.fetched_at


def _order_key(article: Article) -> tuple[datetime, str]:
    """Which article came first. The earliest is the original, later ones are copies."""
    return (_when(article), str(article.id))


def is_near_copy(
    pair: PairScore,
    min_jaccard: float,
    same_outlet_minutes: float,
    cross_outlet_hours: float,
) -> bool:
    """The copy rule, shared by marking, the labelling export and the evaluation.

    Beyond cosine similarity (checked when pairs are found) a near copy needs: enough shared
    wording, publication times close together (one outlet listing a page twice does it within
    minutes, other outlets may reprint hours later) and figures that do not conflict (a changed
    death toll means an update, which is not safe to hide)."""
    if pair.jaccard < min_jaccard:
        return False
    older, newer = sorted((pair.a, pair.b), key=_order_key)
    gap_minutes = (_when(newer) - _when(older)).total_seconds() / 60
    allowed = same_outlet_minutes if older.source_id == newer.source_id else cross_outlet_hours * 60
    if gap_minutes > allowed:
        return False
    return not figures_conflict(dedup_text(older), dedup_text(newer))


def mark_duplicates(
    db: Session,
    model_name: str,
    min_cosine: float,
    min_jaccard: float,
    per_article: int = 5,
    same_outlet_minutes: float = 30.0,
    cross_outlet_hours: float = 6.0,
) -> DedupResult:
    """Recompute `is_duplicate_of_id` from scratch. Same data and thresholds, same answer."""
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

    # 2) Near copies.
    for pair in find_pairs(db, model_name, min_cosine, per_article):
        if not is_near_copy(pair, min_jaccard, same_outlet_minutes, cross_outlet_hours):
            continue
        older, newer = sorted((pair.a, pair.b), key=_order_key)
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
