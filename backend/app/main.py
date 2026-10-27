from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.sources import router as sources_router
from app.db.session import engine

app = FastAPI(title="No Fake World API")
app.include_router(sources_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
