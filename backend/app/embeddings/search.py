import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Article, ArticleEmbedding, Source
from app.embeddings.model import Embedder


@dataclass(frozen=True)
class SearchHit:
    article_id: uuid.UUID
    title: str
    source: str
    url: str
    published_at: datetime | None
    score: float  # cosine similarity: higher means closer in meaning


def vector_search(db: Session, embedder: Embedder, query: str, limit: int = 10) -> list[SearchHit]:
    query_vector = embedder.embed_query(query)
    distance = ArticleEmbedding.embedding.cosine_distance(query_vector)
    rows = db.execute(
        select(Article, Source.name, distance.label("distance"))
        .join(ArticleEmbedding, ArticleEmbedding.article_id == Article.id)
        .join(Source, Source.id == Article.source_id)
        .where(ArticleEmbedding.model_name == embedder.name)
        .order_by(distance)
        .limit(limit)
    ).all()
    return [
        SearchHit(a.id, a.title, source_name, a.url, a.published_at, 1.0 - float(dist))
        for a, source_name, dist in rows
    ]
