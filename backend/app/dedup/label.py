import argparse
import csv
import uuid

from app.db.models import Article
from app.db.session import SessionLocal
from app.dedup.export_pairs import CSV_PATH, FIELDS, STORY_CSV_PATH

PROMPTS = {
    "copy": "Type 1 = same piece of writing, 0 = different report, s = skip, q = save and quit.",
    "story": (
        "Type 1 = SAME news development (even if written separately), 0 = different events,\n"
        "s = skip (keeps the current label), q = save and quit.\n"
        "Ask: are both mainly about the same development? Same topic, different development = 0."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["copy", "story"], default="copy")
    parser.add_argument("--review", choices=["0", "1"], help="re-judge pairs labelled 0 or 1")
    args = parser.parse_args()
    path = STORY_CSV_PATH if args.kind == "story" else CSV_PATH

    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if args.review:
        todo = [row for row in rows if row["label"].strip() == args.review]
        print(f"reviewing {len(todo)} pairs currently labelled {args.review}.")
    else:
        todo = [row for row in rows if not row["label"].strip()]
        print(f"{len(todo)} unlabelled pairs.")
    print(PROMPTS[args.kind])
    try:
        with SessionLocal() as db:
            for number, row in enumerate(todo, start=1):
                print(f"\n--- pair {number}/{len(todo)} (same outlet: {row['same_source']}) ---")
                for tag, key in (("A", "id_a"), ("B", "id_b")):
                    article = db.get(Article, uuid.UUID(row[key]))
                    if article is None:
                        continue
                    stamp = article.published_at
                    when = stamp.strftime("%d %b %H:%M") if stamp else "no date"
                    text = (article.body_text or article.snippet or "")[:500].replace("\n", " ")
                    print(f"{tag}: [{when}] {article.title}\n   {text}")
                answer = input("label [1/0/s/q]: ").strip().lower()
                if answer == "q":
                    break
                if answer in {"0", "1"}:
                    row["label"] = answer
    finally:
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        done = sum(1 for row in rows if row["label"].strip())
        print(f"\nsaved. {done} of {len(rows)} pairs labelled.")


if __name__ == "__main__":
    main()
