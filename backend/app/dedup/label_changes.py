import csv
import io
import subprocess

from app.dedup.export_pairs import CSV_PATH


def _read(text: str) -> dict[tuple[str, str], dict[str, str]]:
    rows = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    return {(row["id_a"], row["id_b"]): row for row in rows}


def main() -> None:
    """Compare my current labels with the last commit, so no slip goes unnoticed."""
    repo = CSV_PATH.parents[1]
    relative = CSV_PATH.relative_to(repo).as_posix()
    committed = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=repo,
        check=True,
    ).stdout
    old = _read(committed)
    new = _read(CSV_PATH.read_text(encoding="utf-8-sig"))
    changed = [
        (old[key]["label"], row["label"], row)
        for key, row in new.items()
        if key in old and old[key]["label"] != row["label"]
    ]
    added = [row for key, row in new.items() if key not in old]
    print(f"labels changed since the last commit: {len(changed)}; new pairs: {len(added)}")
    for before, after, row in sorted(changed, key=lambda item: -float(item[2]["cosine"])):
        print(
            f"{before or '-'} -> {after or '-'}  cos {row['cosine']}  "
            f"{row['title_a'][:45]} | {row['title_b'][:45]}"
        )


if __name__ == "__main__":
    main()
