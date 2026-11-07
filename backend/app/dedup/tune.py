import csv
from pathlib import Path

from app.dedup.export_pairs import CSV_PATH


def load_labeled(path: Path) -> list[tuple[float, float, int]]:
    rows: list[tuple[float, float, int]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            label = row["label"].strip()
            if label in {"0", "1"}:
                rows.append((float(row["cosine"]), float(row["jaccard"]), int(label)))
    return rows


def score(
    rows: list[tuple[float, float, int]], min_cosine: float, min_jaccard: float
) -> tuple[float, float, float, int, int, int]:
    tp = fp = fn = 0
    for cosine, jac, label in rows:
        predicted = cosine >= min_cosine and jac >= min_jaccard
        if predicted and label == 1:
            tp += 1
        elif predicted and label == 0:
            fp += 1
        elif not predicted and label == 1:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, tp, fp, fn


def main() -> None:
    rows = load_labeled(CSV_PATH)
    positives = sum(label for _, _, label in rows)
    print(f"labelled pairs: {len(rows)} (copies: {positives}, different: {len(rows) - positives})")
    if positives < 5:
        print("warning: very few copies labelled, so any threshold is a weak guess")
    results = []
    for cosine_step in range(0, 10):
        for jaccard_step in range(2, 10):
            c, j = round(0.90 + 0.01 * cosine_step, 2), round(0.1 * jaccard_step, 1)
            results.append((score(rows, c, j), c, j))
    results.sort(key=lambda item: (item[0][2], item[0][0], item[1], item[2]), reverse=True)
    print("cosine jaccard | precision recall   f1 |  tp  fp  fn")
    for (precision, recall, f1, tp, fp, fn), c, j in results[:10]:
        print(
            f"{c:.2f}   {j:.1f}     | {precision:9.2f} {recall:6.2f} {f1:5.2f} "
            f"| {tp:3} {fp:3} {fn:3}"
        )


if __name__ == "__main__":
    main()
