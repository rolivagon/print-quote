"""Paper master data model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from quote.repo.models.paper_pricing import PaperPricing


class Paper(SQLModel, table=True):
    """Paper master data."""

    __tablename__ = "papers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    weight: int = Field(description="Gramaje en gramos")
    description: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    deleted_at: datetime | None = Field(default=None, index=True)

    # Relationships
    pricing: list["PaperPricing"] = Relationship(back_populates="paper")
