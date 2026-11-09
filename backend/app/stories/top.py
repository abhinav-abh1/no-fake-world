import argparse
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.db.session import SessionLocal
from app.stories.rank import top_stories


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--min-outlets", type=int, default=settings.edition_min_outlets)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    since = datetime.now(UTC) - timedelta(hours=args.hours)
    with SessionLocal() as db:
        stories = top_stories(db, since, args.min_outlets, args.limit)
        if not stories:
            print("no story meets the publication rule")
        for rank, story in enumerate(stories, start=1):
            print(
                f"{rank:>2}. {story.independent_outlet_count} independent of "
                f"{story.outlet_count} outlets, {story.original_count} originals, "
                f"last {story.last_seen_at:%d %b %H:%M}  {story.title[:70]}"
            )


if __name__ == "__main__":
    main()
