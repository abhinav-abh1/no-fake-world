import argparse
import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.dedup.pairs import find_pairs
from app.embeddings.model import MODEL_NAME

CSV_PATH = Path(__file__).resolve().parents[3] / "evals" / "dedup_pairs.csv"
STORY_CSV_PATH = CSV_PATH.with_name("story_pairs.csv")
FIELDS = ["id_a", "id_b", "cosine", "jaccard", "same_source", "title_a", "title_b", "label"]


def export(db: Session, path: Path, model_name: str, min_cosine: float, max_pairs: int) -> int:
    """Add new candidate pairs to the CSV. Rows you already labelled are kept untouched."""
    rows: dict[tuple[str, str], dict[str, str]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                rows[(row["id_a"], row["id_b"])] = row

    candidates = sorted(find_pairs(db, model_name, min_cosine), key=lambda p: -p.cosine)
    new = [p for p in candidates if (str(p.a.id), str(p.b.id)) not in rows]
    room = max(0, max_pairs - len(rows))
    if room and new:
        step = max(1.0, len(new) / room)  # spread the picks across the whole similarity range
        for index in range(min(room, len(new))):
            pair = new[int(index * step)]
            rows[(str(pair.a.id), str(pair.b.id))] = {
                "id_a": str(pair.a.id),
                "id_b": str(pair.b.id),
                "cosine": f"{pair.cosine:.4f}",
                "jaccard": f"{pair.jaccard:.4f}",
                "same_source": str(pair.a.source_id == pair.b.source_id),
                "title_a": pair.a.title[:120],
                "title_b": pair.b.title[:120],
                "label": "",
            }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(rows.values(), key=lambda r: -float(r["cosine"])):
            writer.writerow(row)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["copy", "story"], default="copy")
    parser.add_argument("--max", type=int)
    parser.add_argument("--min-cosine", type=float)
    args = parser.parse_args()
    story = args.kind == "story"
    path = STORY_CSV_PATH if story else CSV_PATH
    max_pairs = args.max or (80 if story else 60)
    min_cosine = args.min_cosine or (0.82 if story else 0.90)
    with SessionLocal() as db:
        total = export(db, path, MODEL_NAME, min_cosine, max_pairs)
    print(f"{total} pairs in {path}")


if __name__ == "__main__":
    main()
