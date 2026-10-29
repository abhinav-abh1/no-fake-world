from app.db.models import Article, Source
from app.db.session import SessionLocal
from app.embeddings.embed_articles import embed_pending
from app.embeddings.search import vector_search
from tests.fakes import FakeEmbedder

TITLES = [
    "Israel election leaves no clear winner",
    "Lula wins Brazil presidential vote",
    "Cafes must offer mugs instead of takeaway cups",
]


def _add_articles() -> None:
    with SessionLocal() as db:
        source = Source(name="Test", feed_url="https://news.example/rss")
        db.add(source)
        db.commit()
        for index, title in enumerate(TITLES):
            db.add(Article(source_id=source.id, url=f"https://news.example/{index}", title=title))
        db.commit()


def test_embedding_is_idempotent() -> None:
    _add_articles()
    with SessionLocal() as db:
        first = embed_pending(db, FakeEmbedder())
        second = embed_pending(db, FakeEmbedder())
    assert (first.items_out, second.items_out) == (3, 0)


def test_search_ranks_by_closeness() -> None:
    _add_articles()
    with SessionLocal() as db:
        embed_pending(db, FakeEmbedder())
        hits = vector_search(db, FakeEmbedder(), "who won the Israel election", limit=3)
    assert hits[0].title.startswith("Israel election")
    assert hits[0].score > hits[1].score
