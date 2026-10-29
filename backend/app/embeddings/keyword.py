from typing import Any

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ColumnClause

from app.db.models import Article, Source
from app.embeddings.search import SearchHit

ENGLISH: ColumnClause[Any] = literal_column("'english'::regconfig")


def keyword_search(
    db: Session, query: str, limit: int = 30, hide_duplicates: bool = True
) -> list[SearchHit]:
    """Articles that contain ALL the query words (after stemming), best text match first.

    The score is Postgres' text rank. It is NOT comparable with a cosine similarity.
    """
    ts_query = func.websearch_to_tsquery(ENGLISH, query)
    rank = func.ts_rank_cd(Article.search_vector, ts_query)
    stmt = (
        select(Article, Source.name, rank.label("rank"))
        .join(Source, Source.id == Article.source_id)
        .where(Article.search_vector.op("@@")(ts_query))
        .order_by(rank.desc(), Article.published_at.desc().nulls_last())
        .limit(limit)
    )
    if hide_duplicates:
        stmt = stmt.where(Article.is_duplicate_of_id.is_(None))
    rows = db.execute(stmt).all()
    return [
        SearchHit(a.id, a.title, source_name, a.url, a.published_at, float(score))
        for a, source_name, score in rows
    ]
