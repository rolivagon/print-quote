"""Fixed Product models for database persistence."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from quote.repo.models.client import Client


class FixedProduct(SQLModel, table=True):
    """Fixed product created from a saved quote.

    A fixed product stores a snapshot of a quote configuration along with
    predefined quantity ranges and fixed prices. Products can be global
    (client_id=None) or client-specific.
    """

    __tablename__ = "fixed_products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    product_id: str = Field(unique=True, index=True, description="Unique product identifier")
    name: str = Field(description="Product display name")
    print_type: str = Field(index=True, description="Print type: DIGITAL, OFFSET, PLOTTER")
    client_id: int | None = Field(
        default=None,
        foreign_key="clients.id",
        description="Client ID if client-specific, None for global",
    )
    base_quote_snapshot: dict = Field(
        sa_column=Column(JSON),
        description="JSON snapshot of the base quote configuration",
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    # Relationships
    client: "Client" = Relationship(back_populates="fixed_products")
    ranges: list["FixedProductQuantityRange"] = Relationship(
        back_populates="fixed_product",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class FixedProductQuantityRange(SQLModel, table=True):
    """Quantity range with fixed unit price for a fixed product."""

    __tablename__ = "fixed_product_quantity_ranges"

    __table_args__ = (
        UniqueConstraint(
            "fixed_product_id", "min_quantity", "max_quantity", name="uq_product_range"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fixed_product_id: UUID = Field(foreign_key="fixed_products.id", index=True)
    min_quantity: int = Field(ge=1, description="Minimum quantity (inclusive)")
    max_quantity: int = Field(ge=1, description="Maximum quantity (inclusive)")
    unit_price: Decimal = Field(decimal_places=2, description="Fixed unit price for this range")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    fixed_product: FixedProduct = Relationship(back_populates="ranges")
