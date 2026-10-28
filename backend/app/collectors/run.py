from app.collectors.http import make_client
from app.collectors.rss import run_collection
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as db, make_client() as client:
        run = run_collection(db, client)
    print(
        f"status={run.status} entries_seen={run.items_in} "
        f"new_articles={run.items_out} errors={len(run.errors or [])}"
    )


if __name__ == "__main__":
    main()
