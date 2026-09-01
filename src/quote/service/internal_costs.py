"""Database-backed composition of internal production costs."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from quote.domain.enums import PrintType, Unit
from quote.pricing.internal_costs import (
    InternalCost,
    InternalCostBreakdown,
    InternalCostResult,
    calculate_internal_cost,
    calculate_internal_finish_cost,
)
from quote.repo.models import FinishInternalCost, PaperInternalCost


def _rate_data(rate, *, paper: bool = False) -> dict:
    if rate is None:
        return {}
    data = {
        "print_type": rate.print_type.value,
        "unit": rate.unit.value,
    }
    if paper:
        data.update(
            paper_cost=str(rate.paper_cost) if rate.paper_cost is not None else None,
            printing_cost=str(rate.printing_cost) if rate.printing_cost is not None else None,
        )
    else:
        data["unit_cost"] = str(rate.unit_cost)
        data["finish_id"] = rate.finish_id
    return data


def calculate_internal_cost_breakdown(
    db: Session,
    *,
    print_type: PrintType,
    paper_id: int | None,
    finish_ids: list[int],
    quantity: int,
    sheets: int | None,
    billable_sqm: Decimal | None,
) -> InternalCostBreakdown:
    """Load configured rates and calculate all available components."""
    paper_config = None
    if paper_id is not None:
        paper_config = (
            db.execute(
                select(PaperInternalCost).where(
                    PaperInternalCost.paper_id == paper_id,
                    PaperInternalCost.print_type == print_type,
                )
            )
            .scalars()
            .first()
        )

    expected_unit = Unit.SQM if print_type == PrintType.PLOTTER else Unit.SHEET
    configured_unit = paper_config.unit if paper_config else expected_unit
    paper_result = calculate_internal_cost(
        paper_config.paper_cost if paper_config else None,
        configured_unit,
        sheets=sheets,
        billable_sqm=billable_sqm,
        quantity=quantity,
    )
    printing_result = calculate_internal_cost(
        paper_config.printing_cost if paper_config else None,
        configured_unit,
        sheets=sheets,
        billable_sqm=billable_sqm,
        quantity=quantity,
    )

    finish_results = []
    configured_finishes = []
    for finish_id in finish_ids:
        config = (
            db.execute(
                select(FinishInternalCost).where(
                    FinishInternalCost.finish_id == finish_id,
                    FinishInternalCost.print_type == print_type,
                )
            )
            .scalars()
            .first()
        )
        configured_finishes.append(_rate_data(config))
        finish_results.append(
            calculate_internal_finish_cost(
                InternalCost(print_type, config.unit, config.unit_cost) if config else None,
                print_type=print_type,
                quantity=quantity,
                sheets=sheets,
                billable_sqm=billable_sqm,
            )
        )

    finishing_value = (
        sum(
            (result.value for result in finish_results if result.value is not None), Decimal("0.00")
        )
        if any(result.value is not None for result in finish_results)
        else None
    )
    finishing_result = (
        InternalCostResult(
            finishing_value,
            "calculado" if finishing_value is not None else "no indicado",
            expected_unit,
        )
        if finish_results
        else InternalCostResult(Decimal("0.00"), "no_aplica", expected_unit)
    )
    available = [
        result.value
        for result in (paper_result, printing_result, finishing_result)
        if result.value is not None
    ]
    notices = []
    for name, result in (
        ("paper", paper_result),
        ("printing", printing_result),
        ("finishing", finishing_result),
    ):
        if result.value is None and name != "finishing":
            notices.append(f"{name}=no indicado")
    for finish_id, result in zip(finish_ids, finish_results, strict=False):
        if result.value is None:
            notices.append(f"finishing:{finish_id}=no indicado")

    return InternalCostBreakdown(
        print_type=print_type,
        quantity=quantity,
        metrics={"sheets": sheets, "billable_sqm": billable_sqm},
        configured_rates={
            "paper": _rate_data(paper_config, paper=True),
            "finishes": configured_finishes,
        },
        paper=paper_result,
        printing=printing_result,
        finishing=finishing_result,
        total=sum(available, Decimal("0.00")),
        notices=notices,
    )
