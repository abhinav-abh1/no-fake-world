import argparse

from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.model import MODEL_NAME
from app.stories.group import build_stories


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=settings.story_min_similarity)
    parser.add_argument("--window-hours", type=float, default=settings.story_window_hours)
    parser.add_argument("--days", type=int, default=settings.story_days)
    args = parser.parse_args()
    with SessionLocal() as db:
        result = build_stories(db, MODEL_NAME, args.threshold, args.window_hours, args.days)
    print(
        f"stories={result.stories} articles={result.articles} "
        f"largest={result.largest} singletons={result.singletons}"
    )


if __name__ == "__main__":
    main()
