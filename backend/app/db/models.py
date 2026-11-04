import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Postgres builds this column itself from the text columns. Title words count most.
SEARCH_VECTOR_SQL = (
    "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(snippet, '')), 'B') || "
    "setweight(to_tsvector('english', coalesce(left(body_text, 20000), '')), 'C')"
)


class Source(Base):
    """A news outlet or feed we collect from."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    homepage_url: Mapped[str | None] = mapped_column(Text)
    feed_url: Mapped[str] = mapped_column(Text, unique=True)
    country: Mapped[str | None] = mapped_column(String(2))
    language: Mapped[str | None] = mapped_column(String(10))
    lean_hint: Mapped[str | None] = mapped_column(String(20))
    reliability_hint: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    license_notes: Mapped[str | None] = mapped_column(Text)
    robots_ok: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Article(Base):
    """One article as fetched from a source."""

    __tablename__ = "articles"
    __table_args__ = (Index("ix_articles_search_vector", "search_vector", postgresql_using="gin"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(10))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    simhash: Mapped[int | None] = mapped_column(BigInteger)
    is_duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("articles.id"))
    status: Mapped[str] = mapped_column(String(20), server_default="fetched")
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR, Computed(SEARCH_VECTOR_SQL, persisted=True), deferred=True
    )


class RunLog(Base):
    """One run of a pipeline job: what happened and what it cost."""

    __tablename__ = "run_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_name: Mapped[str] = mapped_column(String(100))
    edition_date: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), server_default="running")
    items_in: Mapped[int | None]
    items_out: Mapped[int | None]
    errors: Mapped[list[Any] | None] = mapped_column(JSONB)
    token_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))


class ArticleEmbedding(Base):
    """The meaning of an article as 384 numbers. We store which model made it."""

    __tablename__ = "article_embeddings"
    __table_args__ = (
        Index(
            "ix_article_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    model_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    embedding: Mapped[Any] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Story(Base):
    """A storyline: articles about one news event and its direct developments."""

    __tablename__ = "stories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    article_count: Mapped[int]
    outlet_count: Mapped[int]
    centroid: Mapped[Any] = mapped_column(Vector(384))
    parent_story_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stories.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StoryArticle(Base):
    """Which story an article belongs to. An article is in at most one story."""

    __tablename__ = "story_articles"
    __table_args__ = (Index("ix_story_articles_article_id", "article_id", unique=True),)

    story_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
