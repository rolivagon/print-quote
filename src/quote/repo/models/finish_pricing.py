"""Finish pricing model."""

from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel

from quote.domain.enums import PrintType, Unit
from quote.repo.models.finish import Finish


class FinishPricing(SQLModel, table=True):
    """Finish pricing by quantity range."""

    __tablename__ = "finish_pricing"

    id: int | None = Field(default=None, primary_key=True)
    finish_id: int = Field(foreign_key="finishes.id", index=True)
    print_type: PrintType
    unit: Unit
    min_quantity: int = Field(ge=1)
    max_quantity: int | None = Field(default=None)
    unit_price: Decimal = Field(decimal_places=2, max_digits=10)

    # Relationships
    finish: Finish = Relationship(back_populates="pricing")
