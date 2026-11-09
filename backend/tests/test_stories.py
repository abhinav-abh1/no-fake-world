import uuid
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Article, Source, Story, StoryArticle
from app.db.session import SessionLocal
from app.embeddings.embed_articles import embed_pending
from app.stories.group import (
    Candidate,
    build_stories,
    cluster_labels,
    independent_outlets,
    match_clusters,
    rebuild_recent,
)
from app.stories.rank import top_stories
from tests.fakes import FakeEmbedder


def _unit(*values: float) -> np.ndarray:
    vector = np.array(values, dtype=float)
    return vector / np.linalg.norm(vector)


def test_similar_vectors_share_a_cluster() -> None:
    vectors = np.array(
        [_unit(1, 0, 0), _unit(1, 0.05, 0), _unit(0, 1, 0), _unit(0.05, 1, 0), _unit(0, 0, 1)]
    )
    labels = cluster_labels(vectors, np.zeros(5), min_similarity=0.9, window_hours=72)
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert len(set(labels.tolist())) == 3


def test_articles_far_apart_in_time_are_not_grouped() -> None:
    vectors = np.array([_unit(1, 0, 0), _unit(1, 0, 0)])
    near = cluster_labels(vectors, np.array([0.0, 10.0]), min_similarity=0.9, window_hours=72)
    far = cluster_labels(vectors, np.array([0.0, 200.0]), min_similarity=0.9, window_hours=72)
    assert near[0] == near[1]
    assert far[0] != far[1]


def test_build_stories_counts_outlets_and_rebuilds_cleanly() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        outlet_a = Source(name="A", feed_url="https://a.example/rss")
        outlet_b = Source(name="B", feed_url="https://b.example/rss")
        db.add_all([outlet_a, outlet_b])
        db.commit()
        titles = [
            (outlet_a, "Israel election leaves no clear winner"),
            (outlet_b, "Israel election results show no clear winner"),
            (outlet_a, "Football club signs young striker on record fee"),
            (outlet_b, "Tropical storm approaches the coast of Florida"),
        ]
        for number, (source, title) in enumerate(titles):
            db.add(
                Article(
                    source_id=source.id,
                    url=f"https://news.example/{number}",
                    title=title,
                    published_at=now,
                )
            )
        db.commit()
        embed_pending(db, FakeEmbedder())

        result = build_stories(db, FakeEmbedder.name, 0.5, 72, 1)
        again = build_stories(db, FakeEmbedder.name, 0.5, 72, 1)

        assert (result.stories, result.largest, result.singletons) == (3, 2, 2)
        assert again.stories == 3
        pair = db.scalars(select(Story).where(Story.article_count == 2)).one()
        assert pair.outlet_count == 2
        assert db.scalar(select(func.count()).select_from(Story)) == 3
        assert db.scalar(select(func.count()).select_from(StoryArticle)) == 4


def _add(db: Session, source: Source, number: int, title: str, when: datetime) -> None:
    db.add(
        Article(
            source_id=source.id,
            url=f"https://news.example/{number}",
            title=title,
            published_at=when,
        )
    )


def test_matching_keeps_the_id_when_a_story_grows_or_splits() -> None:
    story_id = uuid.uuid4()
    articles = [uuid.uuid4() for _ in range(7)]
    grown = [set(articles[:5]), {articles[6]}]
    assert match_clusters(grown, {story_id: set(articles[:4])}) == {0: story_id}
    split = [set(articles[:4]), set(articles[4:6])]
    assert match_clusters(split, {story_id: set(articles[:6])}) == {0: story_id}


def test_story_id_survives_a_rebuild_when_the_story_grows() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        outlet_a = Source(name="A", feed_url="https://a.example/rss")
        outlet_b = Source(name="B", feed_url="https://b.example/rss")
        db.add_all([outlet_a, outlet_b])
        db.commit()
        _add(db, outlet_a, 1, "Israel election leaves no clear winner", now)
        _add(db, outlet_b, 2, "Israel election results show no clear winner", now)
        _add(db, outlet_a, 3, "Football club signs young striker on record fee", now)
        db.commit()
        embed_pending(db, FakeEmbedder())
        rebuild_recent(db, FakeEmbedder.name, 0.5, 72, now=now)
        story_id = db.scalars(select(Story).where(Story.article_count == 2)).one().id

        _add(db, outlet_b, 4, "Israel election ends with no clear winner", now)
        db.commit()
        embed_pending(db, FakeEmbedder())
        result = rebuild_recent(db, FakeEmbedder.name, 0.5, 72, now=now)

        grown = db.get(Story, story_id)
        assert grown is not None
        assert grown.article_count == 3
        assert (result.created, result.removed) == (0, 0)
        assert db.scalar(select(func.count()).select_from(StoryArticle)) == 4


def test_old_stories_are_frozen_and_never_deleted() -> None:
    now = datetime.now(UTC)
    old = now - timedelta(days=10)
    with SessionLocal() as db:
        outlet = Source(name="A", feed_url="https://a.example/rss")
        db.add(outlet)
        db.commit()
        _add(db, outlet, 1, "Israel election leaves no clear winner", old)
        _add(db, outlet, 2, "Israel election results show no clear winner", old)
        _add(db, outlet, 3, "Football club signs young striker on record fee", now)
        db.commit()
        embed_pending(db, FakeEmbedder())
        rebuild_recent(db, FakeEmbedder.name, 0.5, 72, since=now - timedelta(days=15), now=now)
        old_story_id = db.scalars(select(Story).where(Story.article_count == 2)).one().id

        again = rebuild_recent(db, FakeEmbedder.name, 0.5, 72, now=now)

        assert again.frozen == 1
        assert again.created == 0
        assert db.get(Story, old_story_id) is not None


def _candidate(source: uuid.UUID, copy_of: uuid.UUID | None = None) -> Candidate:
    return Candidate(
        uuid.uuid4(), source, "t", datetime.now(UTC), np.ones(3), copy_of, copy_of is not None
    )


def test_outlets_that_reprint_each_other_count_once() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    members = [_candidate(a), _candidate(b, copy_of=a), _candidate(c), _candidate(c)]
    assert independent_outlets(members) == 2


def test_a_reprint_is_in_the_story_but_not_an_independent_outlet() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        outlets = [Source(name=name, feed_url=f"https://{name}.example/rss") for name in "ABC"]
        db.add_all(outlets)
        db.commit()
        a, b, c = outlets
        _add(db, a, 1, "Israel election leaves no clear winner", now)
        _add(db, b, 2, "Israel election leaves no clear winner", now)
        _add(db, c, 3, "Israel election results show no clear winner", now)
        db.commit()
        by_outlet = {article.source_id: article for article in db.scalars(select(Article))}
        by_outlet[b.id].is_duplicate_of_id = by_outlet[a.id].id
        db.commit()
        embed_pending(db, FakeEmbedder())

        rebuild_recent(db, FakeEmbedder.name, 0.5, 72, now=now)

        story = db.scalars(select(Story)).one()
        assert (story.article_count, story.original_count) == (3, 2)
        assert (story.outlet_count, story.independent_outlet_count) == (3, 2)


def test_top_stories_applies_the_publication_rule_and_ranks() -> None:
    now = datetime.now(UTC)

    def story(title: str, independent: int, originals: int, seen: datetime) -> Story:
        return Story(
            title=title,
            first_seen_at=seen,
            last_seen_at=seen,
            article_count=originals,
            outlet_count=independent,
            independent_outlet_count=independent,
            original_count=originals,
            centroid=[0.0] * 384,
        )

    with SessionLocal() as db:
        db.add_all(
            [
                story("A", 4, 10, now),
                story("B", 3, 5, now),
                story("C", 2, 20, now),
                story("D", 5, 8, now - timedelta(days=3)),
            ]
        )
        db.commit()
        ranked = top_stories(db, now - timedelta(hours=24), min_outlets=3, limit=10)
        assert [s.title for s in ranked] == ["A", "B"]
