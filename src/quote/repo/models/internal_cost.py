"""Internal production-cost catalog models."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from quote.domain.enums import PrintType, Unit

if TYPE_CHECKING:
    from quote.repo.models.finish import Finish
    from quote.repo.models.paper import Paper


class PaperInternalCost(SQLModel, table=True):
    __tablename__ = "paper_internal_costs"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="papers.id", index=True)
    print_type: PrintType
    unit: Unit
    paper_cost: Decimal | None = Field(default=None, decimal_places=2, max_digits=12, ge=0)
    printing_cost: Decimal | None = Field(default=None, decimal_places=2, max_digits=12, ge=0)
    paper: "Paper" = Relationship(back_populates="internal_costs")


class FinishInternalCost(SQLModel, table=True):
    __tablename__ = "finish_internal_costs"

    id: int | None = Field(default=None, primary_key=True)
    finish_id: int = Field(foreign_key="finishes.id", index=True)
    print_type: PrintType
    unit: Unit
    unit_cost: Decimal = Field(decimal_places=2, max_digits=12, ge=0)
    finish: "Finish" = Relationship(back_populates="internal_costs")
