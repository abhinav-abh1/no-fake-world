import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.embeddings.keyword import keyword_search
from app.embeddings.model import Embedder
from app.embeddings.search import SearchHit, vector_search

RRF_K = 60  # the usual constant: it keeps one top rank from dominating


def fuse(rankings: list[list[uuid.UUID]], k: int = RRF_K) -> list[tuple[uuid.UUID, float]]:
    """Reciprocal rank fusion: every list an article appears in adds 1 / (k + its position)."""
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for position, article_id in enumerate(ranking, start=1):
            scores[article_id] = scores.get(article_id, 0.0) + 1.0 / (k + position)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


@dataclass(frozen=True)
class HybridHit:
    article_id: uuid.UUID
    title: str
    source: str
    url: str
    published_at: datetime | None
    score: float  # fused score: only useful for ordering
    vector_score: float | None  # cosine similarity, if the meaning search saw it
    keyword_rank: int | None  # 1 = best keyword match, None = keyword search did not match


def hybrid_search(
    db: Session,
    embedder: Embedder,
    query: str,
    limit: int = 10,
    min_vector_score: float = 0.80,
    pool: int = 30,
    hide_duplicates: bool = True,
) -> list[HybridHit]:
    vector_hits = vector_search(db, embedder, query, limit=pool, hide_duplicates=hide_duplicates)
    keyword_hits = keyword_search(db, query, limit=pool, hide_duplicates=hide_duplicates)

    # "No good match" rule: a meaning-only match must be close enough; a keyword match always counts
    credible = [hit for hit in vector_hits if hit.score >= min_vector_score]

    details: dict[uuid.UUID, SearchHit] = {
        hit.article_id: hit for hit in [*credible, *keyword_hits]
    }
    vector_scores = {hit.article_id: hit.score for hit in vector_hits}
    keyword_ranks = {hit.article_id: rank for rank, hit in enumerate(keyword_hits, start=1)}
    fused = fuse([[hit.article_id for hit in credible], [hit.article_id for hit in keyword_hits]])

    results: list[HybridHit] = []
    for article_id, score in fused[:limit]:
        detail = details[article_id]
        results.append(
            HybridHit(
                article_id,
                detail.title,
                detail.source,
                detail.url,
                detail.published_at,
                score,
                vector_scores.get(article_id),
                keyword_ranks.get(article_id),
            )
        )
    return results
