from app.collectors.seed_sources import SEED_SOURCES, seed
from app.db.session import SessionLocal
from app.schemas import SourceCreate


def test_seed_is_idempotent() -> None:
    with SessionLocal() as db:
        assert seed(db) == len(SEED_SOURCES)
        assert seed(db) == 0


def test_seed_rows_pass_api_validation() -> None:
    for row in SEED_SOURCES:
        SourceCreate(**row)
