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


_NUMBER_WORDS = {
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "dozen": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
}  # fmt: skip  ("one" is left out on purpose: "no one", "one of the")


def figures(text: str) -> frozenset[str]:
    """Numbers a text mentions, as digits ("33", "1,200") and small number words ("five")."""
    found = {match.replace(",", "") for match in re.findall(r"\d+(?:[.,]\d+)*", text)}
    found |= {_NUMBER_WORDS[word] for word in _WORD.findall(text.lower()) if word in _NUMBER_WORDS}
    return frozenset(found)


def figures_conflict(first: str, second: str) -> bool:
    """True when both texts give figures and neither set contains the other, for example a death
    toll that changed between two versions of a story. Extra figures in only one text (a date)
    are not a conflict."""
    a, b = figures(first), figures(second)
    return bool(a) and bool(b) and not a <= b and not b <= a
