"""Pydantic schemas for the API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from quote.domain.enums import (
    ClientType,
    ColorMode,
    PrintType,
    QuoteStatus,
    Unit,
    UserRole,
)


# Base schema for all API models
class EnumSchema(BaseModel):
    """Base schema for API models with enum support."""

    model_config = ConfigDict(from_attributes=True)


# User schemas
class UserBase(EnumSchema):
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool = True

    @field_serializer("role")
    def serialize_role(self, role: UserRole) -> str:
        """Serialize role enum to string value."""
        return role.value if hasattr(role, "value") else str(role)


class UserInvite(UserBase):
    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        """Ensure only admin or vendedor roles can be assigned via API."""
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Super admin role cannot be assigned via API")
        return v


class UserUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole | None) -> UserRole | None:
        """Ensure only admin or vendedor roles can be assigned via API."""
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Super admin role cannot be assigned via API")
        return v


class UserPasswordUpdate(BaseModel):
    password: str = Field(
        min_length=12,
        max_length=128,
        json_schema_extra={"writeOnly": True, "format": "password"},
    )


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Client schemas
class ClientBase(EnumSchema):
    tax_id: str
    client_type: ClientType
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None

    @field_serializer("client_type")
    def serialize_client_type(self, client_type: ClientType) -> str:
        """Serialize client_type enum to string value."""
        return client_type.value if hasattr(client_type, "value") else str(client_type)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None


class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Paper schemas
class PaperBase(BaseModel):
    name: str
    weight: int
    description: str | None = None
    is_active: bool = True


class PaperCreate(PaperBase):
    pass


class PaperUpdate(BaseModel):
    name: str | None = None
    weight: int | None = None
    description: str | None = None
    is_active: bool | None = None


class Paper(PaperBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Finish schemas
class FinishBase(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class FinishCreate(FinishBase):
    pass


class FinishUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class Finish(FinishBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Paper Pricing schemas
class PaperPricingBase(EnumSchema):
    print_type: PrintType
    min_quantity: int = Field(..., ge=1)
    max_quantity: int | None = None
    unit_price: Decimal

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)


class PaperPricingCreate(PaperPricingBase):
    pass


class PaperPricingUpdate(BaseModel):
    print_type: PrintType | None = None
    min_quantity: int | None = Field(default=None, ge=1)
    max_quantity: int | None = None
    unit_price: Decimal | None = None


class PaperPricing(PaperPricingBase):
    id: int
    paper_id: int

    model_config = ConfigDict(from_attributes=True)


# Finish Pricing schemas
class FinishPricingBase(EnumSchema):
    print_type: PrintType
    unit: Unit
    min_quantity: int = Field(..., ge=1)
    max_quantity: int | None = None
    unit_price: Decimal

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)

    @field_serializer("unit")
    def serialize_unit(self, unit: Unit) -> str:
        """Serialize unit enum to string value."""
        return unit.value if hasattr(unit, "value") else str(unit)


class FinishPricingCreate(FinishPricingBase):
    pass


class FinishPricingUpdate(BaseModel):
    print_type: PrintType | None = None
    unit: Unit | None = None
    min_quantity: int | None = Field(default=None, ge=1)
    max_quantity: int | None = None
    unit_price: Decimal | None = None


class FinishPricing(FinishPricingBase):
    id: int
    finish_id: int

    model_config = ConfigDict(from_attributes=True)


# Dimension schemas
class Dimensions(BaseModel):
    """Dimensions in centimeters."""

    width_cm: float = Field(..., gt=0, description="Width in centimeters")
    height_cm: float = Field(..., gt=0, description="Height in centimeters")


# Geometry configuration
class GeometryConfig(BaseModel):
    """Geometry configuration for imposition calculations."""

    bleed_mm: float = Field(default=0, ge=0, description="Bleed in millimeters")
    margin_mm: float = Field(default=0, ge=0, description="Margin in millimeters")
    gap_mm: float = Field(default=0, ge=0, description="Gap between pieces in millimeters")
    allow_rotate: bool = Field(default=True, description="Allow rotation for better packing")


# Sheet configuration
class SheetConfig(BaseModel):
    """Sheet/plate configuration."""

    usable_width_cm: float = Field(..., gt=0, description="Usable width in centimeters")
    usable_height_cm: float = Field(..., gt=0, description="Usable height in centimeters")


# Finish item for quote calculation
class QuoteFinishItem(BaseModel):
    """Finish item for quote calculation."""

    finish_id: int = Field(..., gt=0, description="Finish ID")
    quantity: int = Field(default=1, ge=1, description="Quantity (for ojetillos, etc.)")


# Base quote calculation request
class QuoteCalculateBase(EnumSchema):
    """Base quote calculation request."""

    print_type: PrintType = Field(..., description="Type of printing")
    quantity: int = Field(..., gt=0, description="Quantity to print")
    dimensions: Dimensions = Field(..., description="Piece dimensions")
    finishes: list[QuoteFinishItem] = Field(default_factory=list, description="Finishes to apply")
    loss_percentage: float = Field(default=0, ge=0, le=100, description="Loss percentage")
    vat_rate: float = Field(default=19, ge=0, le=100, description="VAT rate percentage")

    @field_validator("print_type", mode="before")
    @classmethod
    def validate_print_type(cls, v):
        """Ensure print_type is properly converted to enum."""
        if isinstance(v, str):
            try:
                return PrintType(v)
            except ValueError:
                raise ValueError(f"Invalid print_type: {v}")
        return v


# Digital quote calculation request
class DigitalQuoteCalculate(QuoteCalculateBase):
    """Digital printing quote calculation request."""

    print_type: PrintType = PrintType.DIGITAL
    paper_id: int = Field(..., gt=0, description="Paper ID")
    color_mode: ColorMode = Field(..., description="Color mode (4/0, 4/4)")
    geometry: GeometryConfig = Field(default_factory=GeometryConfig, description="Geometry config")
    sheet_config: SheetConfig = Field(..., description="Sheet configuration")

    @field_validator("color_mode", mode="before")
    @classmethod
    def validate_color_mode(cls, v):
        """Ensure color_mode is properly converted to enum."""
        if isinstance(v, str):
            try:
                return ColorMode(v)
            except ValueError:
                raise ValueError(f"Invalid color_mode: {v}")
        return v


# Plotter quote calculation request
class PlotterQuoteCalculate(QuoteCalculateBase):
    """Plotter printing quote calculation request."""

    print_type: PrintType = PrintType.PLOTTER
    material_type: str = Field(..., description="Material type (sintetico, lona_pvc, etc.)")
    minimum_m2: float = Field(default=0.5, gt=0, description="Minimum square meters to charge")


# Offset quote calculation request
class OffsetQuoteCalculate(QuoteCalculateBase):
    """Offset printing quote calculation request."""

    print_type: PrintType = PrintType.OFFSET
    paper_id: int = Field(..., gt=0, description="Paper ID")
    color_mode: ColorMode = Field(..., description="Color mode (4/0, 4/4)")
    num_designs: int = Field(default=1, ge=1, description="Number of different designs")
    merma_per_design: int = Field(default=0, ge=0, description="Waste sheets per design")
    geometry: GeometryConfig = Field(default_factory=GeometryConfig, description="Geometry config")
    sheet_config: SheetConfig = Field(..., description="Sheet configuration")

    @field_validator("color_mode", mode="before")
    @classmethod
    def validate_color_mode(cls, v):
        """Ensure color_mode is properly converted to enum."""
        if isinstance(v, str):
            try:
                return ColorMode(v)
            except ValueError:
                raise ValueError(f"Invalid color_mode: {v}")
        return v

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)

    @field_serializer("color_mode")
    def serialize_color_mode(self, color_mode: ColorMode) -> str:
        """Serialize color_mode enum to string value."""
        return color_mode.value if hasattr(color_mode, "value") else str(color_mode)


# Union type for quote calculation
QuoteCalculateRequest = DigitalQuoteCalculate | PlotterQuoteCalculate | OffsetQuoteCalculate


# Calculation breakdown detail
class CalculationBreakdown(BaseModel):
    """Detailed breakdown of quote calculations."""

    # Packing info (digital/offset)
    pieces_per_sheet: int | None = Field(None, ge=0, description="Pieces per sheet")
    sheets_needed: int | None = Field(None, ge=0, description="Sheets needed")
    total_sheets_with_merma: int | None = Field(None, ge=0, description="Total sheets with waste")

    # Plotter specific
    square_meters: float | None = Field(None, ge=0, description="Square meters (plotter)")
    billable_square_meters: float | None = Field(None, ge=0, description="Billable square meters")

    # Cost components
    material_cost: Decimal = Field(..., ge=0, description="Material cost")
    finishing_cost: Decimal = Field(..., ge=0, description="Finishing cost")
    plates_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Plates cost (offset)")
    run_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Run cost (offset)")
    fixed_costs: Decimal = Field(default=Decimal("0"), ge=0, description="Fixed costs")
    paper_cost: Decimal = Field(default=Decimal("0"), ge=0, description="Paper cost")

    # Totals
    subtotal_before_markup: Decimal = Field(..., ge=0, description="Subtotal before markup")
    markup_applied: Decimal = Field(..., ge=0, description="Markup amount applied")
    subtotal_with_markup: Decimal = Field(..., ge=0, description="Subtotal with markup")
    net_before_iva: Decimal = Field(..., ge=0, description="Net amount before IVA")
    iva_amount: Decimal = Field(..., ge=0, description="IVA amount")
    total_final: Decimal = Field(..., gt=0, description="Final total")


# Quote calculation response
class QuoteCalculateResponse(EnumSchema):
    """Quote calculation response with full details."""

    print_type: PrintType = Field(..., description="Type of printing")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    breakdown: CalculationBreakdown = Field(..., description="Calculation breakdown")

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)


# Quote item for creation (simplified - backend calculates everything)
class QuoteItemCreate(EnumSchema):
    """Quote item creation schema - simplified payload.

    The backend automatically calculates:
    - pieces_per_sheet, sheets_needed
    - material_cost, finishing_cost
    - IVA (19%), total_final
    """

    name: str = Field(..., min_length=1, description="Item name")
    description: str | None = Field(None, description="Item description")
    print_type: PrintType = Field(..., description="Type of printing")
    color_mode: ColorMode = Field(..., description="Color mode")
    quantity: int = Field(..., gt=0, description="Quantity to print")

    # Dimensions
    width_cm: float = Field(..., gt=0, description="Width in centimeters")
    height_cm: float = Field(..., gt=0, description="Height in centimeters")

    # Material (for digital/offset)
    paper_id: int | None = Field(None, gt=0, description="Paper ID (for digital/offset)")

    # Material type (for plotter)
    material_type: str | None = Field(None, description="Material type (for plotter)")

    # Minimum square meters (for plotter)
    minimum_m2: float = Field(
        default=0.5, gt=0, description="Minimum square meters to charge (for plotter)"
    )

    # Sheet configuration (digital/offset)
    sheet_config: SheetConfig | None = Field(None, description="Sheet configuration")

    # Finishes (only IDs, quantities come from pricing ranges)
    finishes: list[int] = Field(default_factory=list, description="Finish IDs")

    # Loss percentage (optional, default 0%)
    loss_percentage: float = Field(default=0, ge=0, le=100, description="Loss percentage (0-100)")

    # Offset specific
    num_designs: int = Field(default=1, ge=1, description="Number of designs (offset)")
    merma_per_design: int = Field(default=0, ge=0, description="Waste sheets per design (offset)")

    @field_validator("print_type", mode="before")
    @classmethod
    def validate_print_type(cls, v):
        """Ensure print_type is properly converted to enum."""
        if isinstance(v, str):
            try:
                return PrintType(v)
            except ValueError:
                raise ValueError(f"Invalid print_type: {v}")
        return v

    @field_validator("color_mode", mode="before")
    @classmethod
    def validate_color_mode(cls, v):
        """Ensure color_mode is properly converted to enum."""
        if isinstance(v, str):
            try:
                return ColorMode(v)
            except ValueError:
                raise ValueError(f"Invalid color_mode: {v}")
        return v

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)

    @field_serializer("color_mode")
    def serialize_color_mode(self, color_mode: ColorMode) -> str:
        """Serialize color_mode enum to string value."""
        return color_mode.value if hasattr(color_mode, "value") else str(color_mode)


# Nested schemas for calculation details
class DimensionsInfo(BaseModel):
    """Dimensions information."""

    width_cm: Decimal = Field(..., description="Width in centimeters")
    height_cm: Decimal = Field(..., description="Height in centimeters")


class PaperInfo(BaseModel):
    """Paper information."""

    id: int | None = Field(None, description="Paper ID")
    name: str | None = Field(None, description="Paper name")


class FinishInfo(BaseModel):
    """Finish information with calculated cost."""

    id: int = Field(..., description="Finish ID")
    name: str = Field(..., description="Finish name")
    unit_price: str = Field(..., description="Unit price in CLP format")
    unit: str | None = Field(None, description="Unit of measurement")
    calculated_cost: str = Field(..., description="Calculated cost in CLP format")


class Specifications(EnumSchema):
    """Item specifications."""

    print_type: PrintType = Field(..., description="Type of printing")
    quantity: int = Field(..., description="Quantity")
    dimensions: DimensionsInfo = Field(..., description="Dimensions")
    color_mode: ColorMode = Field(..., description="Color mode")
    paper: PaperInfo = Field(..., description="Paper information")
    finishes: list[FinishInfo] = Field(
        default_factory=list, description="List of finishes with costs"
    )

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)

    @field_serializer("color_mode")
    def serialize_color_mode(self, color_mode: ColorMode) -> str:
        """Serialize color_mode enum to string value."""
        return color_mode.value if hasattr(color_mode, "value") else str(color_mode)


class PackingInfo(BaseModel):
    """Packing calculation information."""

    pieces_per_sheet: int | None = Field(None, description="Pieces per sheet")
    sheets_needed: int | None = Field(None, description="Sheets needed")


class PricingInfo(BaseModel):
    """Pricing information."""

    paper_unit_price: Decimal = Field(..., description="Paper unit price")
    currency: str = Field(default="CLP", description="Currency")


class ProductionCalculation(BaseModel):
    """Production calculation details."""

    packing: PackingInfo = Field(..., description="Packing calculation")
    pricing: PricingInfo = Field(..., description="Pricing information")


class DirectCosts(BaseModel):
    """Direct costs breakdown."""

    material: str = Field(..., description="Material cost in CLP format")
    finishing: str = Field(..., description="Finishing cost in CLP format")
    total_direct_costs: str = Field(..., description="Total direct costs in CLP format")


class OffsetSpecificCosts(BaseModel):
    """Offset-specific costs (only applicable for offset printing)."""

    plates: str = Field(default="$0", description="Plates cost in CLP format")
    printing_run: str = Field(default="$0", description="Printing run cost in CLP format")
    fixed_costs: str = Field(default="$0", description="Fixed costs in CLP format")


class CostBreakdown(BaseModel):
    """Complete cost breakdown."""

    direct_costs: DirectCosts = Field(..., description="Direct costs")
    offset_specific_costs: OffsetSpecificCosts = Field(
        default_factory=OffsetSpecificCosts, description="Offset-specific costs"
    )


class MarkupInfo(BaseModel):
    """Markup calculation information."""

    rate_percentage: float = Field(..., description="Markup rate percentage")
    amount: str = Field(..., description="Markup amount in CLP format")
    base_amount: str = Field(..., description="Base amount before markup in CLP format")
    subtotal_with_markup: str = Field(..., description="Subtotal with markup in CLP format")


class LossesInfo(BaseModel):
    """Losses information (optional)."""

    percentage: float = Field(default=0, description="Loss percentage")
    amount: str = Field(default="$0", description="Loss amount in CLP format")


class PricingCalculation(BaseModel):
    """Pricing calculation details."""

    markup: MarkupInfo = Field(..., description="Markup calculation")
    losses: LossesInfo = Field(default_factory=LossesInfo, description="Losses information")


class IvaInfo(BaseModel):
    """IVA (VAT) information."""

    rate_percentage: float = Field(default=19, description="IVA rate percentage")
    amount: str = Field(..., description="IVA amount in CLP format")
    subtotal_with_iva: str = Field(..., description="Subtotal with IVA in CLP format")


class FinalTotals(BaseModel):
    """Final totals calculation."""

    subtotal_net: str = Field(..., description="Net subtotal in CLP format")
    iva: IvaInfo = Field(..., description="IVA information")
    final_total_rounded: str = Field(..., description="Final total rounded in CLP format")


class CalculationDetails(BaseModel):
    """Complete calculation details for a quote item."""

    specifications: Specifications = Field(..., description="Item specifications")
    production_calculation: ProductionCalculation = Field(..., description="Production calculation")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown")
    pricing_calculation: PricingCalculation = Field(..., description="Pricing calculation")
    final_totals: FinalTotals = Field(..., description="Final totals")


# Quote creation request
class QuoteCreateRequest(EnumSchema):
    """Create quote request."""

    client_id: int = Field(..., gt=0, description="Client ID")
    items: list[QuoteItemCreate] = Field(..., min_length=1, description="Quote items")


# Quote item response with calculation details
class QuoteItemResponse(EnumSchema):
    """Quote item response with full calculation details."""

    id: int = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str | None = Field(None, description="Item description")
    calculation_details: CalculationDetails = Field(..., description="Complete calculation details")

    # Legacy fields for backward compatibility (deprecated)
    print_type: PrintType = Field(..., description="Type of printing")
    color_mode: ColorMode = Field(..., description="Color mode")

    @field_serializer("print_type")
    def serialize_print_type(self, print_type: PrintType) -> str:
        """Serialize print_type enum to string value."""
        return print_type.value if hasattr(print_type, "value") else str(print_type)

    @field_serializer("color_mode")
    def serialize_color_mode(self, color_mode: ColorMode) -> str:
        """Serialize color_mode enum to string value."""
        return color_mode.value if hasattr(color_mode, "value") else str(color_mode)

    paper_id: int | None = Field(None, description="Paper ID")
    width: Decimal = Field(..., description="Width")
    height: Decimal = Field(..., description="Height")
    quantity: int = Field(..., description="Quantity")
    paper_unit_price: str = Field(..., description="Paper unit price in CLP format")
    pieces_per_sheet: int | None = Field(None, description="Pieces per sheet")
    sheets_needed: int | None = Field(None, description="Sheets needed")
    total_sheets_with_merma: int | None = Field(None, description="Total sheets with waste")
    square_meters: Decimal | None = Field(None, description="Square meters (plotter)")
    material_cost: str = Field(..., description="Material cost in CLP format")
    finishing_cost: str = Field(..., description="Finishing cost in CLP format")
    plates_cost: str = Field(default="$0", description="Plates cost in CLP format (offset)")
    run_cost: str = Field(default="$0", description="Run cost in CLP format (offset)")
    fixed_costs: str = Field(default="$0", description="Fixed costs in CLP format")
    paper_cost: str = Field(default="$0", description="Paper cost in CLP format")
    loss_percentage: float = Field(default=0, description="Loss percentage applied")
    subtotal_before_losses: str = Field(..., description="Subtotal before losses in CLP format")
    subtotal_with_losses: str = Field(..., description="Subtotal after losses in CLP format")
    iva_amount: str = Field(..., description="IVA amount in CLP format")
    total_final: str = Field(..., description="Final total in CLP format")

    model_config = ConfigDict(from_attributes=True)


# Quote response
class QuoteResponse(EnumSchema):
    """Quote response with CLP formatted amounts."""

    id: int = Field(..., description="Quote ID")
    quote_number: str = Field(..., description="Quote number")
    status: QuoteStatus = Field(..., description="Quote status")

    @field_serializer("status")
    def serialize_status(self, status: QuoteStatus) -> str:
        """Serialize status enum to string value."""
        return status.value if hasattr(status, "value") else str(status)

    seller_id: UUID = Field(..., description="Seller UUID who created the quote")
    client_id: int = Field(..., description="Client ID")
    client: Client | None = Field(None, description="Client information")
    subtotal: str = Field(..., description="Subtotal amount in CLP format ($1.234.567,89)")
    tax: str = Field(..., description="Tax amount in CLP format ($1.234.567,89)")
    total: str = Field(..., description="Total amount in CLP format ($1.234.567,89)")
    items: list[QuoteItemResponse] = Field(default_factory=list, description="Quote items")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# Quote status update
class QuoteStatusUpdate(EnumSchema):
    """Quote status update request."""

    status: QuoteStatus = Field(..., description="New status")

    @field_serializer("status")
    def serialize_status(self, status: QuoteStatus) -> str:
        """Serialize status enum to string value."""
        return status.value if hasattr(status, "value") else str(status)


# Quote list filters
class QuoteListFilters(EnumSchema):
    """Filters for listing quotes."""

    status: QuoteStatus | None = Field(None, description="Filter by status")
    client_id: int | None = Field(None, description="Filter by client")
    skip: int = Field(default=0, ge=0, description="Skip N records")
    limit: int = Field(default=50, ge=1, le=100, description="Limit results")


# Fixed Product schemas
class FixedProductRangeCreate(BaseModel):
    """Schema for creating a quantity range."""

    min_qty: int = Field(..., ge=1, description="Minimum quantity")
    max_qty: int = Field(..., ge=1, description="Maximum quantity")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit")


class FixedProductRangeResponse(BaseModel):
    """Schema for quantity range response."""

    id: str = Field(..., description="Range UUID")
    min_qty: int = Field(..., description="Minimum quantity")
    max_qty: int = Field(..., description="Maximum quantity")
    unit_price: str = Field(..., description="Price per unit in CLP format")


class FixedProductCreate(BaseModel):
    """Schema for creating a fixed product from a quote."""

    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    name: str = Field(..., min_length=1, description="Product name")
    client_id: int | None = Field(None, description="Client ID if client-specific")


class FixedProductFromQuoteRequest(BaseModel):
    """Request to create a fixed product from quote data."""

    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    name: str = Field(..., min_length=1, description="Product name")
    client_id: int | None = Field(None, description="Client ID if client-specific")
    quote_data: QuoteCalculateRequest = Field(..., description="Quote calculation data")


class FixedProductSnapshot(BaseModel):
    """Snapshot of base quote configuration."""

    reference_quantity: int = Field(..., description="Reference quantity used")
    dimensions: DimensionsInfo = Field(..., description="Product dimensions")
    color_mode: str = Field(..., description="Color mode")
    paper: PaperInfo = Field(..., description="Paper information")
    finishes: list[FinishInfo] = Field(default_factory=list, description="Finishes")
    pieces_per_sheet: int | None = Field(None, description="Pieces per sheet")


class FixedProductResponse(EnumSchema):
    """Response schema for fixed product."""

    id: str = Field(..., description="Product UUID")
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    print_type: str = Field(..., description="Print type")
    client_id: int | None = Field(None, description="Client ID if client-specific")
    snapshot: FixedProductSnapshot = Field(..., description="Base quote snapshot")
    ranges: list[FixedProductRangeResponse] = Field(
        default_factory=list, description="Quantity ranges"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class FixedProductListResponse(BaseModel):
    """Response for listing fixed products."""

    items: list[FixedProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total count")


class FixedProductQuoteRequest(BaseModel):
    """Request to quote using a fixed product."""

    quantity: int = Field(..., ge=1, description="Quantity to quote")


class FixedProductQuoteResponse(BaseModel):
    """Response for quoting with fixed product."""

    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Requested quantity")
    applied_range: FixedProductRangeResponse | None = Field(None, description="Applied price range")
    unit_price: str = Field(..., description="Unit price in CLP format")
    total_final: str = Field(..., description="Total in CLP format")
    reference_data: dict = Field(default_factory=dict, description="Reference data from base quote")
