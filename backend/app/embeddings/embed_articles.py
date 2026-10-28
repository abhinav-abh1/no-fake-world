import argparse
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Article, ArticleEmbedding, RunLog
from app.db.session import SessionLocal
from app.embeddings.model import E5Embedder, Embedder

BODY_CHARS = 1500  # the opening of the article carries most of its meaning


def embedding_text(article: Article) -> str:
    parts = [article.title]
    body = article.body_text or article.snippet
    if body:
        parts.append(body[:BODY_CHARS])
    return "\n".join(parts)


def embed_pending(
    db: Session, embedder: Embedder, limit: int = 500, batch_size: int = 32
) -> RunLog:
    """Embed articles that have no vector yet for this model. Safe to run repeatedly."""
    run = RunLog(job_name="embed_articles", status="running")
    db.add(run)
    db.commit()

    already_done = (
        select(ArticleEmbedding.article_id)
        .where(
            ArticleEmbedding.article_id == Article.id,
            ArticleEmbedding.model_name == embedder.name,
        )
        .exists()
    )
    articles = list(
        db.scalars(
            select(Article).where(~already_done).order_by(Article.fetched_at.desc()).limit(limit)
        )
    )
    done = 0
    try:
        for start in range(0, len(articles), batch_size):
            batch = articles[start : start + batch_size]
            vectors = embedder.embed_passages([embedding_text(a) for a in batch])
            db.add_all(
                ArticleEmbedding(article_id=a.id, model_name=embedder.name, embedding=v)
                for a, v in zip(batch, vectors, strict=True)
            )
            db.commit()
            done += len(batch)
    except Exception:
        db.rollback()
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        db.commit()
        raise

    run.finished_at = datetime.now(UTC)
    run.items_in = len(articles)
    run.items_out = done
    run.status = "ok"
    db.commit()
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    started = time.perf_counter()
    embedder = E5Embedder()
    loaded = time.perf_counter()
    with SessionLocal() as db:
        run = embed_pending(db, embedder, limit=args.limit)
    finished = time.perf_counter()
    print(
        f"status={run.status} embedded={run.items_out} "
        f"model_load={loaded - started:.1f}s embedding={finished - loaded:.1f}s"
    )


if __name__ == "__main__":
    main()
