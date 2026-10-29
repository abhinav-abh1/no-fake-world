import csv
import uuid

from app.db.models import Article
from app.db.session import SessionLocal
from app.dedup.export_pairs import CSV_PATH, FIELDS


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    todo = [row for row in rows if not row["label"].strip()]
    print(f"{len(todo)} unlabelled pairs.")
    print("Type 1 = same piece of writing, 0 = different report, s = skip, q = save and quit.")
    try:
        with SessionLocal() as db:
            for number, row in enumerate(todo, start=1):
                print(f"\n--- pair {number}/{len(todo)} (same outlet: {row['same_source']}) ---")
                for tag, key in (("A", "id_a"), ("B", "id_b")):
                    article = db.get(Article, uuid.UUID(row[key]))
                    if article is None:
                        continue
                    text = (article.body_text or article.snippet or "")[:500].replace("\n", " ")
                    print(f"{tag}: {article.title}\n   {text}")
                answer = input("label [1/0/s/q]: ").strip().lower()
                if answer == "q":
                    break
                if answer in {"0", "1"}:
                    row["label"] = answer
    finally:
        with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        done = sum(1 for row in rows if row["label"].strip())
        print(f"\nsaved. {done} of {len(rows)} pairs labelled.")


if __name__ == "__main__":
    main()
