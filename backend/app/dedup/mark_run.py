from app.core.config import settings
from app.db.session import SessionLocal
from app.dedup.mark import mark_duplicates
from app.embeddings.model import MODEL_NAME


def main() -> None:
    with SessionLocal() as db:
        result = mark_duplicates(
            db, MODEL_NAME, settings.dedup_min_cosine, settings.dedup_min_jaccard
        )
    print(f"exact={result.exact} near={result.near}")


if __name__ == "__main__":
    main()
