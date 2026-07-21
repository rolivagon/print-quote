"""Paper pricing model."""

from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel

from quote.domain.enums import ColorMode, PrintType
from quote.repo.models.paper import Paper


class PaperPricing(SQLModel, table=True):
    """Paper pricing by print type and quantity range."""

    __tablename__ = "paper_pricing"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="papers.id", index=True)
    print_type: PrintType
    color_mode: ColorMode | None = Field(
        default=None,
        index=True,
        description="NULL = applies to both 4/0 and 4/4",
    )
    min_quantity: int = Field(ge=1)
    max_quantity: int | None = Field(default=None, description="NULL = sin límite superior")
    unit_price: Decimal = Field(decimal_places=2, max_digits=10)

    # Relationships
    paper: Paper = Relationship(back_populates="pricing")
