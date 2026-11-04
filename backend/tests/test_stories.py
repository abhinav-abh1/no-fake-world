from datetime import UTC, datetime

import numpy as np
from sqlalchemy import func, select

from app.db.models import Article, Source, Story, StoryArticle
from app.db.session import SessionLocal
from app.embeddings.embed_articles import embed_pending
from app.stories.group import build_stories, cluster_labels
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
