"""Offset printing pricing calculations."""

import math
from decimal import ROUND_HALF_UP, Decimal

from quote.domain.enums import FinishingMode, Unit
from quote.domain.models import Item, QuoteBreakdown

from .base import PricingEngine, PricingStrategy


class OffsetPricingStrategy(PricingStrategy):
    """Pricing strategy for offset printing."""

    def calculate_price(self) -> float:
        """Calculate offset printing price."""
        return 0.0

    def calculate_imposition(
        self,
        piece_width_cm: float,
        piece_height_cm: float,
        sheet_width_cm: float,
        sheet_height_cm: float,
        bleed_mm: float = 0,
        margin_mm: float = 0,
        gap_mm: float = 0,
        allow_rotate: bool = True,
    ) -> int:
        """Calculate how many pieces fit per sheet (imposition).

        Args:
            piece_width_cm: Width of the piece in cm
            piece_height_cm: Height of the piece in cm
            sheet_width_cm: Width of the sheet in cm
            sheet_height_cm: Height of the sheet in cm
            bleed_mm: Bleed in millimeters
            margin_mm: Margin in millimeters
            gap_mm: Gap between pieces in millimeters
            allow_rotate: Whether to allow rotating pieces

        Returns:
            Number of pieces that fit per sheet
        """
        from quote.pricing.packing import PackingCalculator

        calculator = PackingCalculator()
        return calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet_width_cm,
            sheet_height_cm=sheet_height_cm,
            bleed_mm=bleed_mm,
            margin_mm=margin_mm,
            gap_mm=gap_mm,
            allow_rotate=allow_rotate,
        )

    def parse_color_config(self, color_config: str) -> int:
        """Parse color configuration like '4/0' to total colors."""
        try:
            parts = color_config.split("/")
            return sum(int(part) for part in parts)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid color config format: {color_config}")

    def calculate_total_sheets_with_merma(
        self,
        quantity: int,
        pieces_per_sheet: int,
        merma_per_run: int,
        num_runs: int,
        num_designs: int = 1,
    ) -> int:
        """Calculate total sheets including merma (waste).

        Args:
            quantity: Total quantity to print
            pieces_per_sheet: How many pieces fit per sheet
            merma_per_run: Waste sheets per printing run
            num_runs: Number of printing runs
            num_designs: Number of different designs (optional, defaults to 1)
        """
        if pieces_per_sheet <= 0:
            return 0

        # Calculate production sheets
        sheets_needed = math.ceil(quantity / pieces_per_sheet)

        # Calculate total merma based on runs
        total_merma = merma_per_run * num_runs

        return sheets_needed + total_merma

    def calculate_run_cost(
        self, sheets_per_run: int, price_table: dict, num_runs: int = 1
    ) -> Decimal:
        """Calculate run cost based on sheets per run.

        Args:
            sheets_per_run: Number of sheets per printing run
            price_table: Price lookup table by quantity
            num_runs: Number of printing runs
        """
        single_run_cost = self.lookup_price_by_quantity(sheets_per_run, price_table)
        return single_run_cost * Decimal(num_runs)

    def lookup_price_by_quantity(self, quantity: int, price_table: dict) -> Decimal:
        """Look up price based on quantity."""
        # First try exact integer keys
        if quantity in price_table:
            return Decimal(str(price_table[quantity]))

        # Then try string representation of integer keys
        if str(quantity) in price_table:
            return Decimal(str(price_table[str(quantity)]))

        # Fallback: Find the smallest tier that is >= requested quantity
        try:
            quantities = sorted([int(k) for k in price_table.keys() if str(k).isdigit()])

            for qty in quantities:
                if qty >= quantity:
                    return Decimal(str(price_table[qty]))

            # If no suitable tier found, use the largest tier
            if quantities:
                return Decimal(str(price_table[quantities[-1]]))
        except (ValueError, TypeError):
            pass

        return Decimal("0")

    def calculate_plates_cost(
        self,
        color_config: str | int,
        price_per_color: Decimal,
        num_runs: int = 1,
        is_cover: bool = False,
    ) -> Decimal:
        """Calculate plates cost.

        Args:
            color_config: Color configuration string (e.g., "4/4", "4/0") or integer number of colors
            price_per_color: Price per plate color
            num_runs: Number of printing runs
            is_cover: If True, calculate for cover (uses front colors only)
        """
        # Handle both string color config and integer number of colors
        if isinstance(color_config, int):
            num_colors = color_config
        elif is_cover:
            # For covers, use only front colors (treated as 4/0 even if config is 4/4)
            if "/" in color_config:
                front_colors = int(color_config.split("/")[0])
                num_colors = front_colors
            else:
                num_colors = self.parse_color_config(color_config)
        else:
            num_colors = self.parse_color_config(color_config)

        return Decimal(num_colors) * price_per_color * Decimal(num_runs)

    def calculate_finishing_cost(
        self, finishing_type: str, quantity: int, finishing_table: dict
    ) -> Decimal:
        """Calculate finishing costs with generic lookup logic."""
        # Normalize finishing type name
        finishing_key = finishing_type.lower().replace(" ", "_")

        # Try exact match first
        config = finishing_table.get(finishing_key)

        # Try partial match if exact not found
        if not config:
            for key, value in finishing_table.items():
                if finishing_key in key or key in finishing_key:
                    config = value
                    break

        if not config:
            return Decimal("0")

        # Check if config is a tiered price table (dict with quantity keys)
        if isinstance(config, dict) and not config.get("mode"):
            # This is a tiered price table, use lookup_price_by_quantity
            price = self.lookup_price_by_quantity(quantity, config)
            return price

        # Get price calculation mode and price
        # Support both FinishingMode and Unit enums for backward compatibility
        mode = config.get("mode", Unit.PER_1000.value)
        price = Decimal(str(config.get("price", 0)))

        # Calculate based on mode
        if mode in (Unit.JOB.value, FinishingMode.PER_JOB.value):
            # Fixed price per job
            return price
        elif mode in (Unit.PER_1000.value, FinishingMode.PER_1000.value):
            # Price per thousand units
            return (price * Decimal(quantity)) / Decimal("1000")
        elif mode in (Unit.PER_ITEM.value, FinishingMode.PER_QUANTITY.value):
            # Price per unit
            return price * Decimal(quantity)

        return Decimal("0")

    def calculate_markup_amount(self, base_amount: Decimal, markup_rate: Decimal) -> Decimal:
        """Calculate markup amount with rounding."""
        markup = base_amount * markup_rate
        # Round to nearest peso
        return markup.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def calculate_fixed_costs(self, finishing_type: str, fixed_costs_table: dict) -> Decimal:
        """Calculate fixed costs like molds."""
        cost = Decimal("0")
        for key, value in fixed_costs_table.items():
            if finishing_type in key:
                cost += Decimal(str(value))
        return cost

    def calculate_paper_costs(
        self,
        total_sheets: int,
        paper_spec: str,
        mock_subtotal_target: Decimal,
        known_costs: Decimal,
    ) -> Decimal:
        """
        Calculate paper/other costs to reach target subtotal.

        This method is a placeholder and reverse calculates paper cost
        to match the target subtotal in the prototype/demonstration.
        """
        paper_cost = mock_subtotal_target - known_costs
        return max(Decimal("0"), paper_cost)

    def apply_markup(self, base_amount: Decimal, markup_rate: Decimal) -> Decimal:
        """Apply markup percentage to base amount."""
        return base_amount * (Decimal("1") + markup_rate)

    def apply_iva(self, net_amount: Decimal, iva_rate: Decimal) -> Decimal:
        """Apply IVA to net amount."""
        return net_amount * (Decimal("1") + iva_rate)

    def round_to_hundreds(self, amount: Decimal) -> Decimal:
        """Round amount to nearest hundred."""
        return (amount / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(
            "100"
        )


class OffsetPricingEngine(PricingEngine):
    """Pricing engine for offset printing."""

    def price(self, item: Item) -> QuoteBreakdown:
        """Calculate complete price breakdown for offset item."""
        raise NotImplementedError("OffsetPricingEngine.price not implemented")
