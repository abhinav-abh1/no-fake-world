import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models import Source
from app.schemas import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[SourceRead])
def list_sources(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Source]:
    stmt = select(Source).order_by(Source.name).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: DbSession) -> Source:
    source = Source(**payload.model_dump())
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="a source with this feed_url already exists",
        ) from exc
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: uuid.UUID, db: DbSession) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    return source
