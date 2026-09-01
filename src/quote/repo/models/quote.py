"""Quote models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

from quote.domain.enums import ColorMode, PrintType, QuoteStatus


class Quote(SQLModel, table=True):
    """Quote header model."""

    __tablename__ = "quotes"

    id: int | None = Field(default=None, primary_key=True)
    quote_number: str = Field(index=True, unique=True)
    status: QuoteStatus = Field(default=QuoteStatus.DRAFT)

    # Foreign keys
    seller_id: UUID = Field(foreign_key="users.id")
    client_id: int = Field(foreign_key="clients.id")

    # Totals
    subtotal: Decimal = Field(default=Decimal("0.00"), decimal_places=2, max_digits=12)
    tax: Decimal = Field(default=Decimal("0.00"), decimal_places=2, max_digits=12)
    total: Decimal = Field(default=Decimal("0.00"), decimal_places=2, max_digits=12)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    sent_at: datetime | None = None

    # Relationships
    seller: "User" = Relationship(back_populates="quotes")  # noqa: F821
    client: "Client" = Relationship(back_populates="quotes")  # noqa: F821
    items: list["QuoteItem"] = Relationship(back_populates="quote")


class QuoteItem(SQLModel, table=True):
    """Quote item details with calculation snapshot."""

    __tablename__ = "quote_items"

    id: int | None = Field(default=None, primary_key=True)

    # Foreign keys
    quote_id: int = Field(foreign_key="quotes.id", index=True)
    paper_id: int | None = Field(default=None, foreign_key="papers.id")

    # Item details
    name: str
    description: str | None = None
    print_type: PrintType
    color_mode: ColorMode
    width: Decimal = Field(decimal_places=2, max_digits=8)
    height: Decimal = Field(decimal_places=2, max_digits=8)
    quantity: int = Field(ge=1)

    # Pricing details (snapshot at quote time)
    paper_unit_price: Decimal = Field(decimal_places=2, max_digits=10)

    # Calculation details (snapshot at quote time)
    pieces_per_sheet: int | None = Field(default=None, description="Pieces per sheet")
    sheets_needed: int | None = Field(default=None, description="Sheets needed")
    total_sheets_with_merma: int | None = Field(default=None, description="Total sheets with waste")
    square_meters: Decimal | None = Field(
        default=None, decimal_places=2, max_digits=8, description="Square meters (plotter)"
    )
    material_cost: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Material cost"
    )
    finishing_cost: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Finishing cost"
    )
    plates_cost: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Plates cost (offset)"
    )
    run_cost: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Run cost (offset)"
    )
    fixed_costs: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Fixed costs"
    )
    paper_cost: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Paper cost"
    )
    internal_paper_cost: Decimal | None = Field(default=None, decimal_places=2, max_digits=12)
    internal_printing_cost: Decimal | None = Field(default=None, decimal_places=2, max_digits=12)
    internal_finishing_cost: Decimal | None = Field(default=None, decimal_places=2, max_digits=12)
    internal_cost_total: Decimal | None = Field(default=None, decimal_places=2, max_digits=12)
    internal_cost_snapshot: dict | None = Field(default=None, sa_column=Column(JSON))
    loss_percentage: float = Field(default=0, description="Loss percentage applied")
    subtotal_before_losses: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Subtotal before losses"
    )
    subtotal_with_losses: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Subtotal after losses"
    )
    iva_amount: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="IVA amount"
    )
    total_final: Decimal = Field(
        default=Decimal("0"), decimal_places=2, max_digits=12, description="Final total"
    )

    # JSON snapshot of all calculation details (immutable record of quote at creation time)
    details_json: dict | None = Field(
        default=None, sa_column=Column(JSON), description="Snapshot of calculation details"
    )

    # Relationships
    quote: Quote = Relationship(back_populates="items")
    paper: "Paper" = Relationship()  # noqa: F821
    finishes: list["QuoteItemFinish"] = Relationship(back_populates="quote_item")


class QuoteItemFinish(SQLModel, table=True):
    """Link table between quote items and finishes."""

    __tablename__ = "quote_item_finishes"

    id: int | None = Field(default=None, primary_key=True)
    quote_item_id: int = Field(foreign_key="quote_items.id", index=True)
    finish_id: int = Field(foreign_key="finishes.id")
    unit_price: Decimal = Field(decimal_places=2, max_digits=10)

    # Relationships
    quote_item: QuoteItem = Relationship(back_populates="finishes")
    finish: "Finish" = Relationship()  # noqa: F821
