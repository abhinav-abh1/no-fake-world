import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sqlalchemy import ColumnElement, delete, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.db.models import Article, ArticleEmbedding, RunLog, Story, StoryArticle

WHEN = func.coalesce(Article.published_at, Article.fetched_at)


@dataclass(frozen=True)
class Candidate:
    article_id: uuid.UUID
    source_id: uuid.UUID
    title: str
    when: datetime
    vector: np.ndarray
    copy_source_id: uuid.UUID | None = None
    is_copy: bool = False


@dataclass(frozen=True)
class GroupResult:
    stories: int
    articles: int
    largest: int
    singletons: int


@dataclass(frozen=True)
class RebuildResult:
    candidates: int
    stories: int
    kept: int
    created: int
    removed: int
    frozen: int


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


def group_members(candidates: list[Candidate], labels: np.ndarray) -> list[list[Candidate]]:
    groups: dict[int, list[Candidate]] = {}
    for candidate, number in zip(candidates, labels.tolist(), strict=True):
        groups.setdefault(number, []).append(candidate)
    return list(groups.values())


def independent_outlets(members: list[Candidate]) -> int:
    """Outlets that reprint each other count once: an outlet whose article is a copy of another
    outlet's article inside the same story is joined to that outlet."""
    parent = {m.source_id: m.source_id for m in members}

    def find(outlet: uuid.UUID) -> uuid.UUID:
        while parent[outlet] != outlet:
            parent[outlet] = parent[parent[outlet]]
            outlet = parent[outlet]
        return outlet

    for member in members:
        other = member.copy_source_id
        if other is not None and other in parent and other != member.source_id:
            parent[find(member.source_id)] = find(other)
    return len({find(outlet) for outlet in parent})


def describe(members: list[Candidate]) -> dict[str, Any]:
    """The story fields that come from its articles. The title is the article nearest the
    story's average meaning (a working label, not a neutral headline)."""
    member_vectors = np.vstack([m.vector for m in members])
    centroid = member_vectors.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    closest = members[int(np.argmax(member_vectors @ centroid))]
    return {
        "title": closest.title,
        "first_seen_at": min(m.when for m in members),
        "last_seen_at": max(m.when for m in members),
        "article_count": len(members),
        "outlet_count": len({m.source_id for m in members}),
        "independent_outlet_count": independent_outlets(members),
        "original_count": sum(1 for m in members if not m.is_copy),
        "centroid": centroid.tolist(),
    }


def _load(
    db: Session, model_name: str, condition: ColumnElement[bool], include_copies: bool
) -> list[Candidate]:
    parent = aliased(Article)
    stmt = (
        select(
            Article.id,
            Article.source_id,
            Article.title,
            WHEN,
            ArticleEmbedding.embedding,
            parent.source_id,
            Article.is_duplicate_of_id.is_not(None),
        )
        .join(ArticleEmbedding, ArticleEmbedding.article_id == Article.id)
        .outerjoin(parent, parent.id == Article.is_duplicate_of_id)
        .where(ArticleEmbedding.model_name == model_name, condition)
        .order_by(WHEN, Article.id)
    )
    if not include_copies:
        stmt = stmt.where(Article.is_duplicate_of_id.is_(None))
    rows = db.execute(stmt).all()
    return [
        Candidate(a, s, t, w, np.asarray(v, dtype=float), p, bool(c))
        for a, s, t, w, v, p, c in rows
    ]


def load_candidates(
    db: Session, model_name: str, days: int, include_copies: bool = False
) -> list[Candidate]:
    """Articles that have a vector, from the last `days` days (copies left out by default)."""
    since = datetime.now(UTC) - timedelta(days=days)
    return _load(db, model_name, WHEN >= since, include_copies)


def build_stories(
    db: Session, model_name: str, min_similarity: float, window_hours: float, days: int
) -> GroupResult:
    """Rebuild ALL stories from scratch. Ids change and old stories vanish: experiments only.
    Use rebuild_recent for real runs."""
    run = RunLog(job_name="group_stories", status="running")
    db.add(run)
    candidates = load_candidates(db, model_name, days)
    db.execute(delete(Story))  # story_articles rows go with them (ON DELETE CASCADE)

    sizes: list[int] = []
    if candidates:
        vectors, hours = candidate_arrays(candidates)
        labels = cluster_labels(vectors, hours, min_similarity, window_hours)
        for members in group_members(candidates, labels):
            story = Story(id=uuid.uuid4(), **describe(members))
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


def match_clusters(
    groups: list[set[uuid.UUID]],
    old: dict[uuid.UUID, set[uuid.UUID]],
    min_share: float = 0.5,
) -> dict[int, uuid.UUID]:
    """Which new group continues which old story? A group continues an old story when it holds at
    least `min_share` of that story's articles, so a story that GROWS keeps its id. Each old story
    is used once."""
    scored: list[tuple[float, int, int, uuid.UUID]] = []
    for index, members in enumerate(groups):
        for story_id, old_members in old.items():
            shared = len(members & old_members)
            if shared and old_members:
                scored.append((shared / len(old_members), shared, index, story_id))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    matched: dict[int, uuid.UUID] = {}
    used: set[uuid.UUID] = set()
    for share, _, index, story_id in scored:
        if share < min_share:
            break
        if index in matched or story_id in used:
            continue
        matched[index] = story_id
        used.add(story_id)
    return matched


def rebuild_recent(
    db: Session,
    model_name: str,
    min_similarity: float,
    window_hours: float,
    buffer_hours: float = 24.0,
    since: datetime | None = None,
    now: datetime | None = None,
) -> RebuildResult:
    """Regroup only recent articles and keep the ids of stories that continue.

    Stories whose newest article is older than the cutoff are frozen: never changed or deleted.
    `since` overrides the cutoff to rebuild further back (bootstrapping the history)."""
    run = RunLog(job_name="rebuild_stories", status="running")
    db.add(run)
    now = now or datetime.now(UTC)
    cutoff = since or now - timedelta(hours=window_hours + buffer_hours)

    open_stories = {s.id: s for s in db.scalars(select(Story).where(Story.last_seen_at >= cutoff))}
    frozen = db.scalar(select(func.count()).select_from(Story).where(Story.last_seen_at < cutoff))
    old_members: dict[uuid.UUID, set[uuid.UUID]] = {story_id: set() for story_id in open_stories}
    if open_stories:
        rows = db.execute(
            select(StoryArticle.story_id, StoryArticle.article_id).where(
                StoryArticle.story_id.in_(list(open_stories))
            )
        )
        for story_id, article_id in rows:
            old_members[story_id].add(article_id)
    keep_ids: set[uuid.UUID] = set()
    for old_ids in old_members.values():
        keep_ids |= old_ids  # a story that straddles the cutoff is regrouped as a whole

    condition = WHEN >= cutoff
    if keep_ids:
        condition = or_(condition, Article.id.in_(keep_ids))
    candidates = _load(db, model_name, condition, include_copies=True)

    groups: list[list[Candidate]] = []
    if candidates:
        vectors, hours = candidate_arrays(candidates)
        labels = cluster_labels(vectors, hours, min_similarity, window_hours)
        groups = group_members(candidates, labels)

    matched = match_clusters([{m.article_id for m in g} for g in groups], old_members)
    if open_stories:
        db.execute(delete(StoryArticle).where(StoryArticle.story_id.in_(list(open_stories))))

    created = 0
    for index, members in enumerate(groups):
        fields = describe(members)
        matched_id = matched.get(index)
        if matched_id is None:
            story = Story(id=uuid.uuid4(), **fields)
            db.add(story)
            created += 1
        else:
            story = open_stories[matched_id]
            for name, value in fields.items():
                setattr(story, name, value)
        db.add_all(StoryArticle(story_id=story.id, article_id=m.article_id) for m in members)

    used = set(matched.values())
    removed = [story_id for story_id in open_stories if story_id not in used]
    for story_id in removed:  # merged into another story or dissolved
        db.delete(open_stories[story_id])

    run.finished_at = datetime.now(UTC)
    run.items_in = len(candidates)
    run.items_out = len(groups)
    run.status = "ok"
    db.commit()
    return RebuildResult(
        candidates=len(candidates),
        stories=len(groups),
        kept=len(matched),
        created=created,
        removed=len(removed),
        frozen=frozen or 0,
    )
