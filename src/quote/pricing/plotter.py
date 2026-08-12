"""Plotter printing pricing calculations."""

from dataclasses import dataclass
from decimal import Decimal

from quote.domain.enums import FinishingMode, PlotterBillingMetric, Unit
from quote.domain.models import Item, QuoteBreakdown

from .base import PricingEngine, PricingStrategy
from .money import apply_markup, apply_vat, round_money


class MissingPlotterRateError(ValueError):
    """Raised when the Plotter catalog has no explicit rate for a metric."""


@dataclass(frozen=True)
class PlotterRate:
    """An explicitly published, net-CLP Plotter rate."""

    minimum: Decimal
    maximum: Decimal
    billing_metric: PlotterBillingMetric
    unit_price: Decimal


@dataclass(frozen=True)
class PlotterCharge:
    """The selected Plotter rate, its billing metric, and net amount."""

    rate: PlotterRate
    metric: Decimal
    amount: Decimal


class PlotterPricingStrategy(PricingStrategy):
    """Pricing strategy for plotter printing."""

    def calculate_price(self) -> float:
        """Calculate plotter printing price."""
        pass

    def calculate_square_meters(self, width_cm: float, height_cm: float) -> Decimal:
        """Calculate square meters from cm dimensions."""
        return (Decimal(str(width_cm)) * Decimal(str(height_cm))) / Decimal("10000")

    def billable_sqm(self, width_cm: Decimal, height_cm: Decimal, quantity: int) -> Decimal:
        """Return the approved one-square-metre-minimum metric for the complete job."""
        area = (width_cm * height_cm / Decimal("10000")) * Decimal(quantity)
        return max(Decimal("1"), area)

    def select_rate(
        self,
        rates: list[PlotterRate],
        billing_metric: PlotterBillingMetric,
        metric: Decimal,
    ) -> PlotterRate:
        """Select only a catalog rate that explicitly covers the given metric."""
        for rate in rates:
            if rate.billing_metric == billing_metric and rate.minimum <= metric <= rate.maximum:
                return rate
        raise MissingPlotterRateError(
            f"No explicit Plotter rate for {billing_metric.value} metric {metric}"
        )

    def calculate_amount(
        self,
        rates: list[PlotterRate],
        *,
        quantity: int,
        width_cm: Decimal | None = None,
        height_cm: Decimal | None = None,
    ) -> Decimal:
        """Calculate net CLP from a catalog whose billing metric is unambiguous."""
        return self.calculate_charge(
            rates, quantity=quantity, width_cm=width_cm, height_cm=height_cm
        ).amount

    def calculate_charge(
        self,
        rates: list[PlotterRate],
        *,
        quantity: int,
        width_cm: Decimal | None = None,
        height_cm: Decimal | None = None,
    ) -> PlotterCharge:
        """Select one rate and calculate its net CLP charge for the job."""
        metrics = {rate.billing_metric for rate in rates}
        if len(metrics) != 1:
            raise ValueError("Plotter catalog rates have mixed billing metrics")
        billing_metric = metrics.pop()
        metric = Decimal(quantity)
        if billing_metric == PlotterBillingMetric.SQM:
            if width_cm is None or height_cm is None:
                raise ValueError("width_cm and height_cm are required for square-metre pricing")
            metric = self.billable_sqm(width_cm, height_cm, quantity)
        rate = self.select_rate(rates, billing_metric, metric)
        return PlotterCharge(rate=rate, metric=metric, amount=metric * rate.unit_price)

    def apply_minimum_charge(self, actual_m2: Decimal, minimum_m2: Decimal) -> Decimal:
        """Apply minimum charge for plotter jobs."""
        return max(actual_m2, minimum_m2)

    def calculate_material_cost(
        self, square_meters: Decimal, material_type: str, price_table: dict
    ) -> Decimal:
        """Calculate material cost per square meter."""
        price_per_m2 = self.get_material_price(material_type, price_table)
        return square_meters * price_per_m2

    def calculate_finishing_cost(
        self, finishing_type: str, quantity: int, finishing_prices: dict
    ) -> Decimal:
        """Calculate finishing costs."""
        finishing_config = finishing_prices.get(finishing_type)
        if not finishing_config:
            # Try finding by key that contains name if exact match fails?
            # Or just return 0 if optional?
            # Tests use exact keys usually.
            raise ValueError(f"Finishing type '{finishing_type}' not found in prices.")

        mode = finishing_config.get("mode")
        price = Decimal(str(finishing_config.get("price", 0)))

        # Support both FinishingMode and Unit enums for backward compatibility
        if mode in (Unit.JOB.value, FinishingMode.PER_JOB.value):
            return price
        elif mode in (Unit.PER_ITEM.value, FinishingMode.PER_QUANTITY.value):
            return price * Decimal(quantity)
        elif mode in (Unit.SQM.value, FinishingMode.PER_LINEAR_METER.value):
            # Assuming quantity is meters? Or passed separately?
            # For now assuming quantity covers it or we don't support it yet
            return price * Decimal(quantity)
        else:
            raise ValueError(f"Unknown finishing mode: {mode}")

    def get_material_price(self, material_type: str, price_table: dict) -> Decimal:
        """Get price for material type."""
        if material_type not in price_table:
            raise ValueError(f"Material '{material_type}' not found in price table.")
        return Decimal(str(price_table[material_type]))

    def apply_markup(self, base_amount: Decimal, markup_rate: Decimal) -> Decimal:
        """Apply markup percentage to base amount."""
        return apply_markup(base_amount, markup_rate)

    def apply_iva(self, net_amount: Decimal, iva_rate: Decimal) -> Decimal:
        """Apply IVA to net amount."""
        return apply_vat(net_amount, iva_rate)

    def round_to_hundreds(self, amount: Decimal) -> Decimal:
        """Round amount to nearest hundred."""
        return round_money(amount, "hundreds")


class PlotterPricingEngine(PricingEngine):
    """Pricing engine for plotter printing."""

    def price(self, item: Item) -> QuoteBreakdown:
        """Calculate complete price breakdown for plotter item."""
        raise NotImplementedError("PlotterPricingEngine.price not implemented")
