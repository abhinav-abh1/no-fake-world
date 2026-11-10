from datetime import UTC, datetime, timedelta

from app.db.models import Article, Source
from app.db.session import SessionLocal
from app.dedup.mark import mark_duplicates
from app.dedup.similarity import figures_conflict, jaccard, shingles
from app.embeddings.embed_articles import embed_pending
from tests.fakes import FakeEmbedder

WIRE = (
    "Prime minister announces a new package of measures to reduce energy bills for households, "
    "saying the government will cap prices for two years and fund the plan through a windfall "
    "tax on energy companies, according to officials who briefed reporters on Tuesday."
)
OTHER = (
    "Football club signs a young striker on a five year contract after agreeing a record "
    "transfer fee, with the player expected to join the squad before the start of the season."
)


def _article(
    source: Source, n: int, title: str, snippet: str, minutes: int, content_hash: str | None = None
) -> Article:
    return Article(
        source_id=source.id,
        url=f"https://news.example/{n}",
        title=title,
        snippet=snippet,
        published_at=datetime(2026, 10, 27, 10, 0, tzinfo=UTC) + timedelta(minutes=minutes),
        content_hash=content_hash,
    )


def test_jaccard_separates_copies_from_rewrites() -> None:
    original = shingles(WIRE)
    assert jaccard(original, shingles(WIRE)) == 1.0
    rewrite = shingles(
        "Ministers revealed plans on Tuesday to hold down household energy costs for two years, "
        "paying for it by taxing the profits of power firms."
    )
    assert jaccard(original, rewrite) < 0.2


def test_exact_copies_point_to_the_earliest() -> None:
    with SessionLocal() as db:
        source = Source(name="A", feed_url="https://a.example/rss")
        db.add(source)
        db.commit()
        first = _article(source, 1, "One", WIRE, 0, "a" * 64)
        second = _article(source, 2, "Two", OTHER, 5, "a" * 64)
        db.add_all([first, second])
        db.commit()

        result = mark_duplicates(db, FakeEmbedder.name, 0.9, 0.5)

        db.refresh(first)
        db.refresh(second)
        assert result.exact == 1
        assert first.is_duplicate_of_id is None
        assert second.is_duplicate_of_id == first.id


def test_reprinted_story_is_marked_and_chains_to_the_root() -> None:
    with SessionLocal() as db:
        outlet_a = Source(name="A", feed_url="https://a.example/rss")
        outlet_b = Source(name="B", feed_url="https://b.example/rss")
        db.add_all([outlet_a, outlet_b])
        db.commit()
        first = _article(outlet_a, 1, "PM announces energy bill plan", WIRE, 0)
        copy = _article(outlet_b, 2, "Prime minister announces energy bill plan", WIRE, 30)
        copy2 = _article(outlet_a, 3, "Energy bill plan announced by PM", WIRE, 60)
        other = _article(outlet_b, 4, "Striker signs for club", OTHER, 90)
        everything = [first, copy, copy2, other]
        db.add_all(everything)
        db.commit()
        embed_pending(db, FakeEmbedder())

        result = mark_duplicates(db, FakeEmbedder.name, 0.9, 0.5)
        again = mark_duplicates(db, FakeEmbedder.name, 0.9, 0.5)

        for article in everything:
            db.refresh(article)
        assert first.is_duplicate_of_id is None
        assert copy.is_duplicate_of_id == first.id
        assert copy2.is_duplicate_of_id == first.id
        assert other.is_duplicate_of_id is None
        assert (result.near, again.near) == (2, 2)


def _same_outlet_pair(minutes_apart: int) -> tuple[Article, Article]:
    with SessionLocal() as db:
        source = Source(name="A", feed_url="https://a.example/rss")
        db.add(source)
        db.commit()
        first = _article(source, 1, "PM announces energy bill plan", WIRE, 0)
        second = _article(source, 2, "PM announces energy bill plan", WIRE, minutes_apart)
        db.add_all([first, second])
        db.commit()
        embed_pending(db, FakeEmbedder())
        mark_duplicates(db, FakeEmbedder.name, 0.9, 0.5)
        db.refresh(first)
        db.refresh(second)
        return first, second


def test_same_outlet_relisting_minutes_apart_is_a_copy() -> None:
    first, second = _same_outlet_pair(minutes_apart=5)
    assert second.is_duplicate_of_id == first.id


def test_same_outlet_page_hours_later_is_not_a_copy() -> None:
    _, second = _same_outlet_pair(minutes_apart=180)
    assert second.is_duplicate_of_id is None


def test_conflicting_figures_mean_an_update_not_a_copy() -> None:
    assert figures_conflict("33 killed in strike near Sanaa", "22 killed in strike near Sanaa")
    assert figures_conflict(
        "At least six killed, fifteen injured", "At least five killed, about a dozen injured"
    )
    assert not figures_conflict("At least five killed", "At least 5 killed")
    assert not figures_conflict("A three-nation tour", "A three-nation tour on Friday, November 6")
    assert not figures_conflict("no figures here", "9 killed")


def test_same_text_with_different_figures_is_not_marked_as_a_copy() -> None:
    with SessionLocal() as db:
        source = Source(name="A", feed_url="https://a.example/rss")
        db.add(source)
        db.commit()
        first = _article(source, 1, "33 killed in strike near the capital", WIRE, 0)
        second = _article(source, 2, "22 killed in strike near the capital", WIRE, 0)
        db.add_all([first, second])
        db.commit()
        embed_pending(db, FakeEmbedder())

        result = mark_duplicates(db, FakeEmbedder.name, 0.9, 0.5)

        db.refresh(second)
        assert result.near == 0
        assert second.is_duplicate_of_id is None
