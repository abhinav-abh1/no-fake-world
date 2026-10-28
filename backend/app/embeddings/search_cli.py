import argparse

from app.db.session import SessionLocal
from app.embeddings.model import E5Embedder
from app.embeddings.search import vector_search


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    embedder = E5Embedder()
    with SessionLocal() as db:
        for rank, hit in enumerate(vector_search(db, embedder, args.query, args.limit), start=1):
            print(f"{rank:>2}. {hit.score:.3f}  [{hit.source}]  {hit.title[:90]}")


if __name__ == "__main__":
    main()
