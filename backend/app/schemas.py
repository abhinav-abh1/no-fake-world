import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, TypeAdapter, field_validator

_http_url = TypeAdapter(AnyHttpUrl)


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    feed_url: str = Field(max_length=2000)
    homepage_url: str | None = Field(default=None, max_length=2000)
    country: str | None = Field(default=None, pattern=r"^[A-Za-z]{2}$")
    language: str | None = Field(default=None, max_length=10)
    lean_hint: str | None = Field(default=None, max_length=20)
    reliability_hint: Decimal | None = Field(
        default=None, ge=0, le=1, max_digits=3, decimal_places=2
    )
    license_notes: str | None = None
    robots_ok: bool = False

    @field_validator("feed_url", "homepage_url")
    @classmethod
    def must_be_http_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            _http_url.validate_python(value)
        except ValueError as exc:
            raise ValueError("must be a valid http(s) URL with a host name") from exc
        return value

    @field_validator("country")
    @classmethod
    def country_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    feed_url: str
    homepage_url: str | None
    country: str | None
    language: str | None
    lean_hint: str | None
    reliability_hint: Decimal | None
    license_notes: str | None
    robots_ok: bool
    is_active: bool
    created_at: datetime
