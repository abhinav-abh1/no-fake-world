import csv
import uuid

from app.core.config import settings
from app.db.models import Article
from app.db.session import SessionLocal
from app.dedup.export_pairs import CSV_PATH
from app.dedup.mark import is_near_copy
from app.dedup.pairs import PairScore
from app.dedup.similarity import dedup_text, jaccard, shingles

GROUPS = ("same outlet", "other outlet")


def _report(name: str, counts: dict[str, int]) -> None:
    tp, fp, fn, tn = counts["tp"], counts["fp"], counts["fn"], counts["tn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    total = tp + fp + fn + tn
    detail = f"tp={tp} fp={fp} fn={fn} tn={tn}"
    print(f"{name:<13} labelled {total:>3}  marked {tp + fp:>3}  {detail}")
    print(f"{'':<13} precision {precision:.2f}  recall {recall:.2f}")


def main() -> None:
    """Score the LIVE copy rule on my labelled pairs, separately for pairs from the same outlet
    (is hiding safe?) and from different outlets (shared origin, so not independent?)."""
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["label"].strip() in {"0", "1"}]
    counts = {group: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for group in GROUPS}
    mistakes: list[str] = []
    with SessionLocal() as db:
        for row in rows:
            first = db.get(Article, uuid.UUID(row["id_a"]))
            second = db.get(Article, uuid.UUID(row["id_b"]))
            if first is None or second is None:
                continue
            cosine = float(row["cosine"])
            overlap = jaccard(shingles(dedup_text(first)), shingles(dedup_text(second)))
            marked = cosine >= settings.dedup_min_cosine and is_near_copy(
                PairScore(first, second, cosine, overlap),
                settings.dedup_min_jaccard,
                settings.dedup_same_outlet_minutes,
                settings.dedup_cross_outlet_hours,
            )
            is_copy = row["label"] == "1"
            group = GROUPS[0] if row["same_source"] == "True" else GROUPS[1]
            counts[group][("t" if marked == is_copy else "f") + ("p" if marked else "n")] += 1
            if marked != is_copy:
                gap = -1.0
                if first.published_at and second.published_at:
                    gap = abs((first.published_at - second.published_at).total_seconds()) / 3600
                kind = "FALSE MERGE" if marked else "MISSED COPY"
                mistakes.append(
                    f"{kind}: {gap:5.1f} h apart, {group}, cos {cosine:.3f}  "
                    f"{row['title_a'][:42]} | {row['title_b'][:42]}"
                )
    for group in GROUPS:
        _report(group, counts[group])
    for line in mistakes:
        print(line)


if __name__ == "__main__":
    main()
