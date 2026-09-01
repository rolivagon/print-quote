from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from quote.api.quotes import _internal_breakdown_response
from quote.api.schemas import (
    FinishCreate,
    FinishInternalCostInput,
    PaperCreate,
    PaperInternalCostInput,
)
from quote.domain.enums import PrintType, Unit
from quote.pricing.internal_costs import (
    InternalCost,
    InternalCostBreakdown,
    InternalCostResult,
    calculate_internal_cost,
    calculate_internal_finish_cost,
)
from quote.repo.models import FinishInternalCost, PaperInternalCost
from quote.repo.sql_repo import SQLFinishRepository, SQLPaperRepository
from quote.service.internal_costs import calculate_internal_cost_breakdown


def test_missing_cost_is_not_zero_and_sheet_cost_uses_waste():
    result = calculate_internal_cost(None, Unit.SHEET, sheets=12)

    assert result.value is None
    assert result.status == "no indicado"
    assert calculate_internal_cost(Decimal("2.50"), Unit.SHEET, sheets=12).value == Decimal("30.00")


def test_plotter_finish_sheet_cost_is_incompatible_with_sqm_quote():
    result = calculate_internal_finish_cost(
        InternalCost(print_type=PrintType.PLOTTER, unit=Unit.SHEET, unit_cost=Decimal("10")),
        print_type=PrintType.PLOTTER,
        quantity=4,
        billable_sqm=Decimal("3.2"),
    )

    assert result.value is None
    assert result.status == "no indicado"


@pytest.mark.parametrize(
    ("print_type", "unit", "kwargs", "expected"),
    [
        (PrintType.DIGITAL, Unit.SHEET, {"sheets": 14}, Decimal("28.00")),
        (PrintType.OFFSET, Unit.SHEET, {"sheets": 22}, Decimal("44.00")),
        (PrintType.PLOTTER, Unit.SQM, {"billable_sqm": Decimal("2.5")}, Decimal("5.00")),
    ],
)
def test_internal_material_costs_use_technology_metric(print_type, unit, kwargs, expected):
    result = calculate_internal_cost(Decimal("2"), unit, **kwargs)

    assert result.value == expected


def test_internal_cost_rejects_negative_values():
    with pytest.raises(ValueError, match="non-negative"):
        InternalCost(print_type=PrintType.DIGITAL, unit=Unit.SHEET, unit_cost=Decimal("-1"))


def test_catalog_repositories_store_internal_costs_separately(db_session):
    paper = SQLPaperRepository(db_session).create(
        "Internal paper",
        300,
        internal_costs=[
            {
                "print_type": PrintType.DIGITAL,
                "unit": Unit.SHEET,
                "paper_cost": Decimal("1.25"),
                "printing_cost": Decimal("0.75"),
            }
        ],
    )
    finish = SQLFinishRepository(db_session).create(
        "Internal finish",
        internal_costs=[
            {"print_type": PrintType.PLOTTER, "unit": Unit.SHEET, "unit_cost": Decimal("4.00")}
        ],
    )

    assert isinstance(paper.internal_costs[0], PaperInternalCost)
    assert paper.internal_costs[0].paper_cost == Decimal("1.25")
    assert isinstance(finish.internal_costs[0], FinishInternalCost)
    assert finish.internal_costs[0].unit == Unit.SHEET


def test_catalog_create_rolls_back_master_when_internal_costs_are_invalid(engine):
    with Session(engine) as session:
        repo = SQLPaperRepository(session)
        with pytest.raises(ValueError, match="require unit sqm"):
            repo.create(
                "Atomic invalid paper",
                300,
                internal_costs=[
                    {
                        "print_type": PrintType.PLOTTER,
                        "unit": Unit.SHEET,
                        "paper_cost": Decimal("1"),
                    }
                ],
            )

        assert repo.get_by_name("Atomic invalid paper") is None


def test_api_internal_cost_inputs_reject_negative_money():
    with pytest.raises(ValueError):
        PaperInternalCostInput(
            print_type=PrintType.DIGITAL,
            unit=Unit.SHEET,
            paper_cost=Decimal("-0.01"),
        )


def test_api_rejects_empty_duplicate_and_incompatible_cost_rows():
    with pytest.raises(ValueError, match="must configure"):
        PaperInternalCostInput(print_type=PrintType.DIGITAL, unit=Unit.SHEET)
    with pytest.raises(ValueError, match="require unit sqm"):
        PaperInternalCostInput(
            print_type=PrintType.PLOTTER,
            unit=Unit.SHEET,
            paper_cost=Decimal("0"),
        )
    with pytest.raises(ValueError, match="duplicate"):
        PaperCreate(
            name="Paper",
            weight=100,
            internal_costs=[
                {"print_type": "digital", "unit": "sheet", "paper_cost": 0},
                {"print_type": "digital", "unit": "sheet", "printing_cost": 0},
            ],
        )
    with pytest.raises(ValueError, match="Input should be"):
        FinishCreate(
            name="Finish",
            internal_costs=[{"print_type": "plotter", "unit": "invalid", "unit_cost": 0}],
        )
    with pytest.raises(ValueError, match="only unit sheet"):
        FinishInternalCostInput(print_type=PrintType.DIGITAL, unit=Unit.JOB, unit_cost=0)


def test_internal_breakdown_is_admin_only():
    class Item:
        internal_cost_snapshot = {
            "paper": "$10",
            "printing": "$5",
            "finishing": "$2",
            "total": "$17",
            "notices": [],
        }
        plates_cost = Decimal("3")
        run_cost = Decimal("4")
        fixed_costs = Decimal("0")

    assert _internal_breakdown_response(Item(), False) is None
    result = _internal_breakdown_response(Item(), True)
    assert result is not None
    assert result.total == "$17"
    with pytest.raises(ValueError):
        FinishInternalCostInput(
            print_type=PrintType.PLOTTER,
            unit=Unit.SQM,
            unit_cost=Decimal("-0.01"),
        )


def test_snapshot_keeps_rates_units_metrics_and_results():
    breakdown = InternalCostBreakdown(
        print_type=PrintType.PLOTTER,
        quantity=2,
        metrics={"sheets": None, "billable_sqm": Decimal("3.20")},
        configured_rates={
            "paper": {"print_type": "plotter", "unit": "sqm", "paper_cost": "0.00"},
            "finishes": [{"finish_id": 4, "unit": "sheet", "unit_cost": "10.00"}],
        },
        paper=InternalCostResult(Decimal("0.00"), "calculado", Unit.SQM),
        printing=InternalCostResult(None, "no indicado", Unit.SQM),
        finishing=InternalCostResult(None, "no indicado", Unit.SQM),
        total=Decimal("0.00"),
        notices=["printing=no indicado", "finishing:4=no indicado"],
    )
    snapshot = breakdown.snapshot()

    assert snapshot["configured_rates"]["paper"]["unit"] == "sqm"
    assert snapshot["configured_rates"]["finishes"][0]["finish_id"] == 4
    assert snapshot["metrics"]["billable_sqm"] == "3.20"
    assert snapshot["results"]["paper"]["value"] == "0.00"
    assert snapshot["results"]["printing"]["value"] is None


def test_service_preserves_zero_and_marks_incompatible_finish_missing(db_session):
    paper = SQLPaperRepository(db_session).create(
        "Service paper",
        300,
        internal_costs=[
            {
                "print_type": PrintType.PLOTTER,
                "unit": Unit.SQM,
                "paper_cost": Decimal("0"),
                "printing_cost": Decimal("0"),
            }
        ],
    )
    finish = SQLFinishRepository(db_session).create(
        "Plotter finish",
        internal_costs=[
            {"print_type": PrintType.PLOTTER, "unit": Unit.SHEET, "unit_cost": Decimal("0")}
        ],
    )
    result = calculate_internal_cost_breakdown(
        db_session,
        print_type=PrintType.PLOTTER,
        paper_id=paper.id,
        finish_ids=[finish.id],
        quantity=1,
        sheets=None,
        billable_sqm=Decimal("2.5"),
    )

    assert result.paper.value == Decimal("0.00")
    assert result.printing.value == Decimal("0.00")
    assert result.finishing.value is None
    assert f"finishing:{finish.id}=no indicado" in result.notices
    assert result.total == Decimal("0.00")
