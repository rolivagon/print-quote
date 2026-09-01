"""Internal production-cost calculations shared by quote workflows."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from quote.domain.enums import PrintType, Unit


def validate_paper_unit(print_type: PrintType, unit: Unit) -> None:
    expected = Unit.SQM if print_type == PrintType.PLOTTER else Unit.SHEET
    if unit != expected:
        raise ValueError(f"{print_type.value} paper internal costs require unit {expected.value}")


def validate_finish_unit(print_type: PrintType, unit: Unit) -> None:
    if unit != Unit.SHEET:
        raise ValueError("finish internal costs currently support only unit sheet")


@dataclass(frozen=True)
class InternalCost:
    """A catalogued internal rate, distinct from a selling price."""

    print_type: PrintType
    unit: Unit
    unit_cost: Decimal

    def __post_init__(self) -> None:
        value = Decimal(str(self.unit_cost))
        if value < 0:
            raise ValueError("internal cost must be non-negative")
        object.__setattr__(self, "unit_cost", value.quantize(Decimal("0.01")))


@dataclass(frozen=True)
class InternalCostResult:
    value: Decimal | None
    status: str
    unit: Unit | None = None


@dataclass(frozen=True)
class InternalCostBreakdown:
    """Complete internal-cost result, including audit-ready inputs and metrics."""

    print_type: PrintType
    quantity: int
    metrics: dict[str, Decimal | int | None]
    configured_rates: dict
    paper: InternalCostResult
    printing: InternalCostResult
    finishing: InternalCostResult
    total: Decimal
    notices: list[str] = field(default_factory=list)

    def snapshot(self) -> dict:
        def result_data(result: InternalCostResult) -> dict:
            return {
                "value": str(result.value) if result.value is not None else None,
                "status": result.status,
                "unit": result.unit.value if result.unit else None,
            }

        return {
            "print_type": self.print_type.value,
            "quantity": self.quantity,
            "metrics": {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in self.metrics.items()
            },
            "configured_rates": self.configured_rates,
            "results": {
                "paper": result_data(self.paper),
                "printing": result_data(self.printing),
                "finishing": result_data(self.finishing),
            },
            "total": str(self.total),
            "notices": self.notices,
        }


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_internal_cost(
    unit_cost: Decimal | None,
    unit: Unit,
    *,
    sheets: int | None = None,
    billable_sqm: Decimal | None = None,
    quantity: int | None = None,
) -> InternalCostResult:
    """Calculate a paper/printing component, preserving missing values."""
    if unit_cost is None:
        return InternalCostResult(None, "no indicado", unit)
    rate = InternalCost(PrintType.DIGITAL, unit, unit_cost)
    metric = {
        Unit.SHEET: sheets,
        Unit.SQM: billable_sqm,
        Unit.PER_ITEM: quantity,
        Unit.PER_1000: (Decimal(quantity) / Decimal("1000") if quantity else None),
        Unit.JOB: Decimal("1"),
    }[unit]
    if metric is None:
        return InternalCostResult(None, "no indicado", unit)
    return InternalCostResult(_money(rate.unit_cost * Decimal(str(metric))), "calculado", unit)


def calculate_internal_finish_cost(
    cost: InternalCost | None,
    *,
    print_type: PrintType,
    quantity: int,
    sheets: int | None = None,
    billable_sqm: Decimal | None = None,
) -> InternalCostResult:
    """Calculate a finish only when its technology and unit are compatible."""
    if cost is None or cost.print_type != print_type:
        return InternalCostResult(None, "no indicado")
    if print_type in (PrintType.DIGITAL, PrintType.OFFSET) and cost.unit == Unit.SHEET:
        return calculate_internal_cost(cost.unit_cost, cost.unit, sheets=sheets)
    if print_type == PrintType.PLOTTER and cost.unit == Unit.SQM:
        return calculate_internal_cost(cost.unit_cost, cost.unit, billable_sqm=billable_sqm)
    return InternalCostResult(None, "no indicado", cost.unit)
