import re

from app.db.models import Article

_WORD = re.compile(r"\w+")  # \w also matches Hindi, Malayalam, Arabic and other scripts
BODY_CHARS = 1000
SHINGLE_WORDS = 3


def dedup_text(article: Article) -> str:
    body = article.body_text or article.snippet or ""
    return f"{article.title} {body[:BODY_CHARS]}"


def shingles(text: str, size: int = SHINGLE_WORDS) -> frozenset[tuple[str, ...]]:
    """Every run of `size` consecutive words. Copies share most runs, rewrites share few."""
    words = _WORD.findall(text.lower())
    if len(words) < size:
        return frozenset([tuple(words)]) if words else frozenset()
    return frozenset(tuple(words[i : i + size]) for i in range(len(words) - size + 1))


def jaccard(a: frozenset[tuple[str, ...]], b: frozenset[tuple[str, ...]]) -> float:
    """Overlap between two sets: 1.0 = identical, 0.0 = nothing in common."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
