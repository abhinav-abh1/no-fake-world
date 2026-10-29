import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Article, ArticleEmbedding
from app.dedup.similarity import dedup_text, jaccard, shingles


@dataclass(frozen=True)
class PairScore:
    a: Article
    b: Article
    cosine: float
    jaccard: float


def find_pairs(
    db: Session, model_name: str, min_cosine: float, per_article: int = 5
) -> list[PairScore]:
    """For every article, look at its nearest neighbours and score each pair both ways."""
    rows = db.execute(
        select(ArticleEmbedding.article_id, ArticleEmbedding.embedding).where(
            ArticleEmbedding.model_name == model_name
        )
    ).all()

    found: dict[tuple[uuid.UUID, uuid.UUID], float] = {}
    for article_id, vector in rows:
        distance = ArticleEmbedding.embedding.cosine_distance(vector)
        neighbours = db.execute(
            select(ArticleEmbedding.article_id, distance.label("distance"))
            .where(
                ArticleEmbedding.model_name == model_name,
                ArticleEmbedding.article_id != article_id,
            )
            .order_by(distance)
            .limit(per_article)
        ).all()
        for other_id, dist in neighbours:
            cosine = 1.0 - float(dist)
            if cosine < min_cosine:
                break  # neighbours are sorted, so the rest are even less similar
            key = (min(article_id, other_id), max(article_id, other_id))
            found.setdefault(key, cosine)

    if not found:
        return []
    ids = {article_id for key in found for article_id in key}
    articles = {a.id: a for a in db.scalars(select(Article).where(Article.id.in_(ids)))}
    return [
        PairScore(
            articles[a_id],
            articles[b_id],
            cosine,
            jaccard(shingles(dedup_text(articles[a_id])), shingles(dedup_text(articles[b_id]))),
        )
        for (a_id, b_id), cosine in found.items()
    ]
