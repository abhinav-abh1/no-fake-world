import uuid

from app.db.models import Article, Source
from app.db.session import SessionLocal
from app.embeddings.embed_articles import embed_pending
from app.embeddings.hybrid import fuse, hybrid_search
from app.embeddings.keyword import keyword_search
from tests.fakes import FakeEmbedder

TITLES = [
    "Israel election leaves no clear winner",
    "Lula wins Brazil presidential vote",
    "Election results in Brazil",
    "Voters head to polls in Toronto",
    "Cafes must offer mugs instead of takeaway cups",
]


def _add_articles() -> dict[str, uuid.UUID]:
    with SessionLocal() as db:
        source = Source(name="Test", feed_url="https://news.example/rss")
        db.add(source)
        db.commit()
        articles = [
            Article(source_id=source.id, url=f"https://news.example/{i}", title=title)
            for i, title in enumerate(TITLES)
        ]
        db.add_all(articles)
        db.commit()
        return {a.title: a.id for a in articles}


def test_fuse_rewards_items_found_by_both_lists() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    fused = fuse([[a, b], [b, c]])
    assert fused[0][0] == b


def test_keyword_search_needs_the_words_and_understands_plurals() -> None:
    _add_articles()
    with SessionLocal() as db:
        assert [h.title for h in keyword_search(db, "voter")] == ["Voters head to polls in Toronto"]
        assert keyword_search(db, "venezuela") == []


def test_hybrid_puts_the_match_found_by_both_methods_first() -> None:
    _add_articles()
    with SessionLocal() as db:
        embed_pending(db, FakeEmbedder())
        hits = hybrid_search(db, FakeEmbedder(), "Brazil election", min_vector_score=0.4)
    assert hits[0].title == "Election results in Brazil"
    assert hits[0].keyword_rank == 1
    assert hits[0].vector_score is not None


def test_unrelated_query_returns_no_match() -> None:
    _add_articles()
    with SessionLocal() as db:
        embed_pending(db, FakeEmbedder())
        hits = hybrid_search(db, FakeEmbedder(), "quantum chemistry lecture", min_vector_score=0.4)
    assert hits == []


def test_copies_are_hidden_from_search() -> None:
    ids = _add_articles()
    with SessionLocal() as db:
        copy = db.get(Article, ids["Election results in Brazil"])
        assert copy is not None
        copy.is_duplicate_of_id = ids["Lula wins Brazil presidential vote"]
        db.commit()
        assert keyword_search(db, "Brazil election") == []
        assert len(keyword_search(db, "Brazil election", hide_duplicates=False)) == 1
