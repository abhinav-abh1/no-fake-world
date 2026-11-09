import argparse

from sqlalchemy import select

from app.db.models import Article, Source, Story, StoryArticle
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--members", type=int, default=12)
    args = parser.parse_args()
    with SessionLocal() as db:
        stories = db.scalars(
            select(Story)
            .order_by(Story.outlet_count.desc(), Story.article_count.desc())
            .limit(args.top)
        )
        for story in stories:
            print(f"\n=== {str(story.id)[:8]}  {story.title[:80]}")
            print(
                f"    {story.article_count} articles, {story.outlet_count} outlets, "
                f"{story.first_seen_at:%d %b %H:%M} to {story.last_seen_at:%d %b %H:%M}"
            )
            members = db.execute(
                select(Article.title, Source.name, Article.published_at)
                .join(StoryArticle, StoryArticle.article_id == Article.id)
                .join(Source, Source.id == Article.source_id)
                .where(StoryArticle.story_id == story.id)
                .order_by(Article.published_at)
                .limit(args.members)
            ).all()
            for title, source, stamp in members:
                when = stamp.strftime("%d %b %H:%M") if stamp else "no date"
                print(f"    [{when}] [{source}] {title[:80]}")


if __name__ == "__main__":
    main()
