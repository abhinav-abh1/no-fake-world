import csv
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.hybrid import hybrid_search
from app.embeddings.keyword import keyword_search
from app.embeddings.model import E5Embedder
from app.embeddings.search import vector_search

QUERIES_PATH = Path(__file__).resolve().parents[3] / "evals" / "search_queries.csv"


def main() -> None:
    with QUERIES_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["query"].strip()]
    embedder = E5Embedder()
    summary: list[tuple[str, str, int, float, int]] = []
    with SessionLocal() as db:
        for row in rows:
            query = row["query"].strip()
            keyword = keyword_search(db, query, limit=30)
            vector = vector_search(db, embedder, query, limit=5)
            hybrid = hybrid_search(
                db, embedder, query, limit=5, min_vector_score=settings.search_min_vector_score
            )
            print(f"\n=== {query}  [{row['kind']}]  expect: {row['expect']}")
            print(f"keyword ({len(keyword)} matches, top 5):")
            for hit in keyword[:5]:
                print(f"   {hit.score:.3f} [{hit.source}] {hit.title[:80]}")
            print("vector (top 5):")
            for hit in vector:
                print(f"   {hit.score:.3f} [{hit.source}] {hit.title[:80]}")
            print("hybrid:" if hybrid else "hybrid: no good match")
            for hybrid_hit in hybrid:
                rank = hybrid_hit.keyword_rank or "-"
                print(f"   kw#{rank} [{hybrid_hit.source}] {hybrid_hit.title[:80]}")
            summary.append(
                (query, row["kind"], len(keyword), vector[0].score if vector else 0.0, len(hybrid))
            )
    print("\nSUMMARY")
    print("best_vector  keyword_matches  hybrid_results  kind      query")
    for query, kind, kw_count, best, hybrid_count in summary:
        print(f"{best:11.3f}  {kw_count:15}  {hybrid_count:14}  {kind:<9} {query}")


if __name__ == "__main__":
    main()
