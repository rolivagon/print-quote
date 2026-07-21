"""Finish master data model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from quote.repo.models.finish_pricing import FinishPricing


class Finish(SQLModel, table=True):
    """Finish (terminación) master data."""

    __tablename__ = "finishes"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    deleted_at: datetime | None = Field(default=None, index=True)

    # Relationships
    pricing: list["FinishPricing"] = Relationship(back_populates="finish")
