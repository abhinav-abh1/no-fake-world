import argparse

from app.collectors.extract import extract_pending
from app.collectors.http import make_client
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    with SessionLocal() as db, make_client() as client:
        run = extract_pending(db, client, limit=args.limit)
    print(
        f"status={run.status} tried={run.items_in} extracted={run.items_out} "
        f"errors={len(run.errors or [])}"
    )


if __name__ == "__main__":
    main()
