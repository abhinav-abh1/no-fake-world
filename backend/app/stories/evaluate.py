import argparse
import csv
import uuid
from collections import Counter

from app.core.config import settings
from app.db.session import SessionLocal
from app.dedup.export_pairs import STORY_CSV_PATH
from app.embeddings.model import MODEL_NAME
from app.stories.group import candidate_arrays, cut_tree, linkage_tree, load_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--window-hours", type=float, default=settings.story_window_hours)
    parser.add_argument(
        "--errors", type=float, help="list wrong merges and splits at this similarity"
    )
    args = parser.parse_args()

    with STORY_CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        pairs = [
            (uuid.UUID(row["id_a"]), uuid.UUID(row["id_b"]), int(row["label"]))
            for row in csv.DictReader(handle)
            if row["label"].strip() in {"0", "1"}
        ]
    with SessionLocal() as db:
        candidates = load_candidates(db, MODEL_NAME, args.days)
    index = {c.article_id: i for i, c in enumerate(candidates)}
    usable = [(a, b, label) for a, b, label in pairs if a in index and b in index]
    print(f"articles: {len(candidates)}; labelled pairs used: {len(usable)} of {len(pairs)}")
    if len(candidates) < 2:
        return

    vectors, hours = candidate_arrays(candidates)
    tree = linkage_tree(vectors, hours, args.window_hours)
    print("similarity | stories largest | precision recall   f1 |  tp  fp  fn")
    for step in range(13):
        threshold = 0.80 + 0.01 * step
        labels = cut_tree(tree, threshold)
        sizes = Counter(labels.tolist())
        tp = fp = fn = 0
        for a, b, label in usable:
            together = labels[index[a]] == labels[index[b]]
            if together and label == 1:
                tp += 1
            elif together and label == 0:
                fp += 1
            elif label == 1:
                fn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        left = f"{threshold:.2f}       | {len(sizes):7} {max(sizes.values()):7}"
        print(f"{left} | {precision:9.2f} {recall:6.2f} {f1:5.2f} | {tp:3} {fp:3} {fn:3}")

    if args.errors is not None:
        labels = cut_tree(tree, args.errors)
        titles = {c.article_id: c.title for c in candidates}
        print(f"\nmistakes at similarity {args.errors:.2f}")
        for a, b, label in usable:
            together = labels[index[a]] == labels[index[b]]
            if together and label == 0:
                kind = "WRONG MERGE"
            elif not together and label == 1:
                kind = "SPLIT"
            else:
                continue
            print(f"{kind}: {titles[a][:70]}  |  {titles[b][:70]}")


if __name__ == "__main__":
    main()
