import argparse
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.model import MODEL_NAME
from app.stories.group import rebuild_recent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=settings.story_min_similarity)
    parser.add_argument("--window-hours", type=float, default=settings.story_window_hours)
    parser.add_argument("--buffer-hours", type=float, default=settings.story_buffer_hours)
    parser.add_argument(
        "--since-days", type=float, help="bootstrap: rebuild this many days instead of the window"
    )
    args = parser.parse_args()
    since = datetime.now(UTC) - timedelta(days=args.since_days) if args.since_days else None
    with SessionLocal() as db:
        result = rebuild_recent(
            db,
            MODEL_NAME,
            args.threshold,
            args.window_hours,
            args.buffer_hours,
            since=since,
        )
    print(
        f"candidates={result.candidates} stories={result.stories} kept={result.kept} "
        f"created={result.created} removed={result.removed} frozen={result.frozen}"
    )


if __name__ == "__main__":
    main()
