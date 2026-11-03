import csv
from pathlib import Path

from app.dedup.export_pairs import STORY_CSV_PATH


def load_labeled(path: Path) -> list[tuple[float, int]]:
    rows: list[tuple[float, int]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            label = row["label"].strip()
            if label in {"0", "1"}:
                rows.append((float(row["cosine"]), int(label)))
    return rows


def main() -> None:
    rows = load_labeled(STORY_CSV_PATH)
    same = sum(label for _, label in rows)
    print(f"labelled pairs: {len(rows)} (same story: {same}, different: {len(rows) - same})")
    lowest_same = min((c for c, label in rows if label == 1), default=None)
    highest_diff = max((c for c, label in rows if label == 0), default=None)
    print(f"lowest cosine among same-story pairs:  {lowest_same}")
    print(f"highest cosine among different pairs: {highest_diff}")
    print("\nthreshold | precision recall   f1 |  tp  fp  fn")
    for step in range(0, 19):
        threshold = 0.80 + 0.01 * step
        tp = sum(1 for c, label in rows if c >= threshold and label == 1)
        fp = sum(1 for c, label in rows if c >= threshold and label == 0)
        fn = sum(1 for c, label in rows if c < threshold and label == 1)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        print(
            f"{threshold:.2f}      | {precision:9.2f} {recall:6.2f} {f1:5.2f} "
            f"| {tp:3} {fp:3} {fn:3}"
        )


if __name__ == "__main__":
    main()
