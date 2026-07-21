"""Digital printing pricing calculations."""

from decimal import Decimal

from quote.domain.enums import FinishingMode, Unit
from quote.domain.models import Item, QuoteBreakdown

from .base import PricingEngine, PricingStrategy


class DigitalPricingStrategy(PricingStrategy):
    """Pricing strategy for digital printing."""

    def calculate_price(self) -> float:
        """Calculate digital printing price."""
        pass

    def calculate_sheet_cost(self, sheets: int, color_config: str, price_table: dict) -> Decimal:
        """Calculate cost for sheets based on color configuration."""
        # Get the price ranges for the color configuration
        price_ranges = price_table.get(color_config, [])
        if not price_ranges:
            raise ValueError(f"No price table found for color config: {color_config}")

        # Find the appropriate price per sheet based on quantity
        price_per_sheet = self.lookup_price_by_quantity(sheets, price_ranges)

        # Calculate total cost
        return Decimal(str(sheets)) * price_per_sheet

    def calculate_finishing_cost(
        self, finishing_type: str, quantity: int, finishing_prices: dict
    ) -> Decimal:
        """Calculate finishing costs."""
        finishing_config = finishing_prices.get(finishing_type)
        if not finishing_config:
            raise ValueError(f"No finishing configuration found for: {finishing_type}")

        mode = finishing_config.get("mode")
        price = finishing_config.get("price")

        # Support both FinishingMode and Unit enums for backward compatibility
        if mode in (Unit.JOB.value, FinishingMode.PER_JOB.value):
            # Fixed price per job regardless of quantity
            return price
        elif mode in (Unit.PER_ITEM.value, FinishingMode.PER_QUANTITY.value):
            # Price per unit
            return price * Decimal(str(quantity))
        elif mode in (Unit.PER_1000.value, FinishingMode.PER_1000.value):
            # Price per thousand units
            return price * Decimal(str(quantity)) / Decimal("1000")
        else:
            raise ValueError(f"Unknown finishing mode: {mode}")

    def lookup_price_by_quantity(self, quantity: int, price_ranges: list) -> Decimal:
        """Look up price based on quantity ranges."""
        # price_ranges is a list of tuples: (min_qty, max_qty, price)
        for min_qty, max_qty, price in price_ranges:
            if min_qty <= quantity <= max_qty:
                return price

        # If no range found, raise an error
        raise ValueError(f"No price found for quantity {quantity} in ranges {price_ranges}")

    def apply_markup(self, base_amount: Decimal, markup_rate: Decimal) -> Decimal:
        """Apply markup percentage to base amount."""
        return base_amount * (Decimal("1") + markup_rate)

    def apply_iva(self, net_amount: Decimal, iva_rate: Decimal) -> Decimal:
        """Apply IVA to net amount."""
        return net_amount * (Decimal("1") + iva_rate)

    def round_to_hundreds(self, amount: Decimal) -> Decimal:
        """Round amount to nearest hundred."""
        # Round to nearest hundred using ROUND_HALF_UP
        from decimal import ROUND_HALF_UP

        return (amount / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(
            "100"
        )


class DigitalPricingEngine(PricingEngine):
    """Pricing engine for digital printing."""

    def price(self, item: Item) -> QuoteBreakdown:
        """Calculate complete price breakdown for digital item."""
        raise NotImplementedError("DigitalPricingEngine.price not implemented")
