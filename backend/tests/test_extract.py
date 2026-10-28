import httpx

from app.collectors.extract import extract_pending, extract_text
from app.collectors.http import make_client
from app.db.models import Article, Source
from app.db.session import SessionLocal

ARTICLE_HTML = """<!doctype html><html><head><title>Story</title></head><body>
<nav><a href="/">Home</a><a href="/world">World</a></nav>
<article>
<h1>City council approves new transport plan</h1>
<p>The city council voted on Tuesday to approve a long-awaited transport plan that will add
new bus lanes and extend the tram network across the eastern districts over the next five years.</p>
<p>Supporters said the plan would cut travel times and reduce air pollution, while critics
argued that the cost was too high and that residents had not been consulted enough before
the vote took place.</p>
<p>The mayor said construction would begin next spring and that a public information office
would open this month to answer questions from residents and local businesses affected by
the work.</p>
</article>
<footer>Copyright example.com. All rights reserved.</footer>
</body></html>"""

ALLOW_ALL = "User-agent: *\nAllow: /"
BLOCK_PRIVATE = "User-agent: *\nDisallow: /private"


def _client(robots_txt: str, requested: list[str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots_txt)
        if request.url.path == "/broken":
            return httpx.Response(500)
        return httpx.Response(
            200, text=ARTICLE_HTML, headers={"content-type": "text/html; charset=utf-8"}
        )

    return make_client(httpx.MockTransport(handler))


def _setup(allowed: bool, path: str) -> tuple[Source, Article]:
    with SessionLocal() as db:
        source = Source(name="Test", feed_url="https://news.example/rss", robots_ok=allowed)
        db.add(source)
        db.commit()
        article = Article(source_id=source.id, url=f"https://news.example{path}", title="t")
        db.add(article)
        db.commit()
        return source, article


def _reload(article: Article) -> Article:
    with SessionLocal() as db:
        fresh = db.get(Article, article.id)
        assert fresh is not None
        return fresh


def test_extract_text_finds_the_main_content() -> None:
    text = extract_text(ARTICLE_HTML)
    assert text is not None
    assert "bus lanes" in text
    assert "mayor" in text
    assert "<" not in text


def test_extraction_saves_text_and_hash() -> None:
    _, article = _setup(allowed=True, path="/story")
    requested: list[str] = []
    with SessionLocal() as db:
        run = extract_pending(db, _client(ALLOW_ALL, requested), delay=0)
    saved = _reload(article)
    assert saved.status == "extracted"
    assert saved.body_text is not None
    assert "bus lanes" in saved.body_text
    assert saved.content_hash is not None
    assert len(saved.content_hash) == 64
    assert (run.items_out, run.status) == (1, "ok")


def test_robots_txt_is_respected() -> None:
    _, article = _setup(allowed=True, path="/private/story")
    requested: list[str] = []
    with SessionLocal() as db:
        extract_pending(db, _client(BLOCK_PRIVATE, requested), delay=0)
    assert _reload(article).status == "skipped_robots"
    assert "/private/story" not in requested  # the page itself was never requested


def test_sources_not_enabled_are_never_fetched() -> None:
    _, article = _setup(allowed=False, path="/story")
    requested: list[str] = []
    with SessionLocal() as db:
        extract_pending(db, _client(ALLOW_ALL, requested), delay=0)
    assert _reload(article).status == "fetched"
    assert requested == []  # not even robots.txt


def test_broken_page_is_marked_failed_and_logged() -> None:
    _, article = _setup(allowed=True, path="/broken")
    requested: list[str] = []
    with SessionLocal() as db:
        run = extract_pending(db, _client(ALLOW_ALL, requested), delay=0)
    assert _reload(article).status == "failed"
    assert run.status == "partial"
    assert run.errors is not None
