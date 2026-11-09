from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Story


def top_stories(db: Session, since: datetime, min_outlets: int = 3, limit: int = 10) -> list[Story]:
    """Edition candidates: stories seen since `since` that at least `min_outlets` independent
    outlets reported, ranked by independent outlets, then original articles, then recency."""
    stmt = (
        select(Story)
        .where(Story.last_seen_at >= since, Story.independent_outlet_count >= min_outlets)
        .order_by(
            Story.independent_outlet_count.desc(),
            Story.original_count.desc(),
            Story.last_seen_at.desc(),
        )
        .limit(limit)
    )
    return list(db.scalars(stmt))
