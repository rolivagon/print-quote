"""Domain models for print quote calculations."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from .enums import ColorMode, FinishType, PrintType, Unit


class QuantityRange(BaseModel):
    """Quantity range with fixed unit price for fixed products."""

    min_qty: int = Field(..., ge=1, description="Minimum quantity (inclusive)")
    max_qty: int | None = Field(
        None, ge=1, description="Maximum quantity (inclusive), None for unlimited"
    )
    unit_price: Decimal = Field(..., gt=0, description="Fixed unit price for this range")


class FixedProduct(BaseModel):
    """Fixed product created from a saved quote with quantity-based pricing.

    A fixed product stores a base quote (calculated normally) along with
    predefined quantity ranges and fixed prices. When quoting with a fixed
    product, the total is calculated from the range price, but all other
    breakdown details (pieces_per_sheet, sheets_needed, etc.) are preserved
    from the base quote for reference.
    """

    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product display name")
    base_quote: "QuoteBreakdown" = Field(..., description="Base quote used as reference")
    quantity_ranges: list[QuantityRange] = Field(
        ..., description="List of quantity ranges with prices"
    )
    print_type: PrintType = Field(..., description="Print type (digital/offset/plotter)")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Product attributes for filtering"
    )
    client_id: str | None = Field(None, description="Client ID if client-specific, None for global")


class Size(BaseModel):
    """Size model with width and height in millimeters."""

    width_mm: float = Field(..., gt=0, description="Width in millimeters")
    height_mm: float = Field(..., gt=0, description="Height in millimeters")


class Material(BaseModel):
    """Material model."""

    name: str = Field(..., description="Material name")
    print_type: PrintType | None = Field(None, description="Print type")
    unit: Unit | None = Field(None, description="Unit of measurement")


class Finish(BaseModel):
    """Finish model."""

    type: FinishType = Field(..., description="Finish type")
    unit: Unit = Field(..., description="Unit of measurement")
    price: float = Field(..., ge=0, description="Price per unit")
    mode: str = Field(..., description="Pricing mode: per_job, per_sheet, per_qty, per_1000")


class Item(BaseModel):
    """Item model representing a print job."""

    print_type: PrintType = Field(..., description="Print type")
    size: Size = Field(..., description="Item size")
    color: ColorMode = Field(..., description="Color mode")
    material: Material = Field(..., description="Material specification")
    quantity: int = Field(..., gt=0, description="Quantity to print")
    finishes: list[Finish] = Field(default_factory=list, description="List of finishes")


class MoneyBreakdown(BaseModel):
    """Money breakdown for cost components."""

    material_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Material cost")
    finishing_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Finishing cost")
    plates_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Plates cost (offset)")
    run_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Run cost (offset)")
    fixed_costs: Decimal = Field(default=Decimal("0"), ge=0, description="Fixed costs")
    paper_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Paper cost")
    subtotal_before_markup: Decimal = Field(
        default=Decimal("0"), ge=0, description="Subtotal before markup"
    )
    markup_applied: Decimal = Field(default=Decimal("0"), ge=0, description="Markup amount")
    subtotal_with_markup: Decimal = Field(
        default=Decimal("0"), ge=0, description="Subtotal with markup"
    )
    iva_amount: Decimal = Field(default=Decimal("0"), ge=0, description="IVA amount")
    total_final: Decimal = Field(..., gt=0, description="Final total")


class QuoteBreakdown(BaseModel):
    """Complete quote breakdown with all calculations."""

    print_type: PrintType = Field(..., description="Type of printing")
    quantity: int = Field(..., gt=0, description="Quantity ordered")

    # Packing info
    pieces_per_sheet: int | None = Field(default=None, ge=0, description="Pieces per sheet")
    sheets_needed: int | None = Field(default=None, ge=0, description="Sheets needed")
    total_sheets_with_merma: int | None = Field(
        default=None, ge=0, description="Total sheets including waste"
    )
    square_meters: Decimal | None = Field(default=None, ge=0, description="Square meters (plotter)")

    # Cost breakdown
    material_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Material/sheet cost")
    finishing_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Finishing cost")
    plates_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Plates cost (offset)")
    run_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Run cost (offset)")
    fixed_costs: Decimal = Field(default=Decimal("0"), ge=0, description="Fixed costs")
    paper_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Paper cost")

    # Totals
    subtotal_before_markup: Decimal = Field(
        default=Decimal("0"), ge=0, description="Subtotal before markup"
    )
    markup_applied: Decimal = Field(default=Decimal("0"), ge=0, description="Markup amount")
    subtotal_with_markup: Decimal = Field(
        default=Decimal("0"), ge=0, description="Subtotal with markup"
    )
    iva_amount: Decimal = Field(default=Decimal("0"), ge=0, description="IVA amount")
    total_final: Decimal = Field(..., gt=0, description="Final total")
    net_before_iva: Decimal = Field(default=Decimal("0"), gt=0, description="Net amount before IVA")

    # Fixed product fields
    is_fixed_product: bool = Field(
        default=False, description="Whether this quote uses a fixed product"
    )
    fixed_product_id: str | None = Field(default=None, description="Fixed product ID if applicable")
    applied_range: dict[str, Any] | None = Field(
        default=None, description="Applied quantity range details"
    )
    reference_quantity: int | None = Field(
        default=None, description="Reference quantity from base quote"
    )

    def format_currency(self, amount: Decimal) -> str:
        """Format currency amount."""
        return f"${amount:,.0f}".replace(",", ".")


# Legacy models for backward compatibility
class Quote(BaseModel):
    """Main quote model."""

    pass


class Product(BaseModel):
    """Product model."""

    pass


class Customer(BaseModel):
    """Customer model."""

    pass
