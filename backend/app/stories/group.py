import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import Article, ArticleEmbedding, RunLog, Story, StoryArticle


@dataclass(frozen=True)
class Candidate:
    article_id: uuid.UUID
    source_id: uuid.UUID
    title: str
    when: datetime
    vector: np.ndarray


@dataclass(frozen=True)
class GroupResult:
    stories: int
    articles: int
    largest: int
    singletons: int


def linkage_tree(vectors: np.ndarray, hours: np.ndarray, window_hours: float) -> np.ndarray:
    """Average-linkage tree. Two groups merge only if their members are similar on AVERAGE,
    which stops chains (A close to B, B close to C, but A and C about different things).
    Articles published more than `window_hours` apart count as completely different."""
    unit = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    distance = 1.0 - unit @ unit.T
    gap = np.abs(hours[:, None] - hours[None, :])
    distance[gap > window_hours] = 1.0
    distance = np.clip((distance + distance.T) / 2.0, 0.0, None)
    np.fill_diagonal(distance, 0.0)
    return linkage(squareform(distance, checks=False), method="average")


def cut_tree(tree: np.ndarray, min_similarity: float) -> np.ndarray:
    """Cut the tree where groups are no longer similar enough. One cluster number per article."""
    return np.asarray(fcluster(tree, t=1.0 - min_similarity, criterion="distance"))


def cluster_labels(
    vectors: np.ndarray, hours: np.ndarray, min_similarity: float, window_hours: float
) -> np.ndarray:
    if len(vectors) == 1:
        return np.array([1])
    return cut_tree(linkage_tree(vectors, hours, window_hours), min_similarity)


def candidate_arrays(candidates: list[Candidate]) -> tuple[np.ndarray, np.ndarray]:
    vectors = np.vstack([c.vector for c in candidates])
    hours = np.array([c.when.timestamp() / 3600.0 for c in candidates])
    return vectors, hours


def load_candidates(db: Session, model_name: str, days: int) -> list[Candidate]:
    """Independent (non-copy) articles that have a vector, from the last `days` days."""
    when = func.coalesce(Article.published_at, Article.fetched_at)
    rows = db.execute(
        select(Article.id, Article.source_id, Article.title, when, ArticleEmbedding.embedding)
        .join(ArticleEmbedding, ArticleEmbedding.article_id == Article.id)
        .where(
            ArticleEmbedding.model_name == model_name,
            Article.is_duplicate_of_id.is_(None),
            when >= datetime.now(UTC) - timedelta(days=days),
        )
        .order_by(when, Article.id)
    ).all()
    return [Candidate(a, s, t, w, np.asarray(v, dtype=float)) for a, s, t, w, v in rows]


def build_stories(
    db: Session, model_name: str, min_similarity: float, window_hours: float, days: int
) -> GroupResult:
    """Rebuild all stories from scratch. Story ids change on every run; stable ids come later."""
    run = RunLog(job_name="group_stories", status="running")
    db.add(run)
    candidates = load_candidates(db, model_name, days)
    db.execute(delete(Story))  # story_articles rows go with them (ON DELETE CASCADE)

    sizes: list[int] = []
    if candidates:
        vectors, hours = candidate_arrays(candidates)
        labels = cluster_labels(vectors, hours, min_similarity, window_hours)
        groups: dict[int, list[Candidate]] = {}
        for candidate, number in zip(candidates, labels.tolist(), strict=True):
            groups.setdefault(number, []).append(candidate)
        for members in groups.values():
            member_vectors = np.vstack([m.vector for m in members])
            centroid = member_vectors.mean(axis=0)
            centroid /= np.linalg.norm(centroid)
            closest = members[int(np.argmax(member_vectors @ centroid))]
            story = Story(
                id=uuid.uuid4(),
                title=closest.title,  # the article nearest the story's average meaning
                first_seen_at=min(m.when for m in members),
                last_seen_at=max(m.when for m in members),
                article_count=len(members),
                outlet_count=len({m.source_id for m in members}),
                centroid=centroid.tolist(),
            )
            db.add(story)
            db.add_all(StoryArticle(story_id=story.id, article_id=m.article_id) for m in members)
            sizes.append(len(members))

    run.finished_at = datetime.now(UTC)
    run.items_in = len(candidates)
    run.items_out = len(sizes)
    run.status = "ok"
    db.commit()
    return GroupResult(
        stories=len(sizes),
        articles=len(candidates),
        largest=max(sizes, default=0),
        singletons=sum(1 for size in sizes if size == 1),
    )
