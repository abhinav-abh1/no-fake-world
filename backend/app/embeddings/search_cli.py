import argparse

from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.hybrid import hybrid_search
from app.embeddings.keyword import keyword_search
from app.embeddings.model import E5Embedder
from app.embeddings.search import vector_search


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--mode", choices=["keyword", "vector", "hybrid"], default="hybrid")
    args = parser.parse_args()
    embedder = E5Embedder()
    with SessionLocal() as db:
        if args.mode == "keyword":
            hits = keyword_search(db, args.query, args.limit)
            lines = [f"{h.score:.3f}  [{h.source}]  {h.title[:90]}" for h in hits]
        elif args.mode == "vector":
            hits = vector_search(db, embedder, args.query, args.limit)
            lines = [f"{h.score:.3f}  [{h.source}]  {h.title[:90]}" for h in hits]
        else:
            found = hybrid_search(
                db, embedder, args.query, args.limit, settings.search_min_vector_score
            )
            lines = [
                f"kw#{h.keyword_rank or '-':<2} vec={h.vector_score or 0:.3f}  "
                f"[{h.source}]  {h.title[:80]}"
                for h in found
            ]
    if not lines:
        print("no good match")
    for rank, line in enumerate(lines, start=1):
        print(f"{rank:>2}. {line}")


if __name__ == "__main__":
    main()
