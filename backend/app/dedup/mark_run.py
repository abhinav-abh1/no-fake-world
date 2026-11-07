from app.core.config import settings
from app.db.session import SessionLocal
from app.dedup.mark import mark_duplicates
from app.embeddings.model import MODEL_NAME


def main() -> None:
    with SessionLocal() as db:
        result = mark_duplicates(
            db,
            MODEL_NAME,
            settings.dedup_min_cosine,
            settings.dedup_min_jaccard,
            same_outlet_minutes=settings.dedup_same_outlet_minutes,
            cross_outlet_hours=settings.dedup_cross_outlet_hours,
        )
    print(f"exact={result.exact} near={result.near}")


if __name__ == "__main__":
    main()
