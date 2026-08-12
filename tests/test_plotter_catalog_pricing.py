"""Unit tests for the approved Plotter catalog pricing rules."""

from decimal import Decimal

import pytest

from quote.domain.enums import PlotterBillingMetric
from quote.pricing.plotter import MissingPlotterRateError, PlotterPricingStrategy, PlotterRate


@pytest.fixture
def strategy() -> PlotterPricingStrategy:
    return PlotterPricingStrategy()


@pytest.fixture
def sqm_rates() -> list[PlotterRate]:
    return [
        PlotterRate(Decimal("1.00"), Decimal("5.00"), PlotterBillingMetric.SQM, Decimal("11000")),
        PlotterRate(Decimal("5.01"), Decimal("20.00"), PlotterBillingMetric.SQM, Decimal("8800")),
        PlotterRate(Decimal("20.01"), Decimal("100.00"), PlotterBillingMetric.SQM, Decimal("6600")),
    ]


@pytest.mark.parametrize(
    ("metric", "price"),
    [
        (Decimal("1.00"), Decimal("11000")),
        (Decimal("5.00"), Decimal("11000")),
        (Decimal("5.01"), Decimal("8800")),
        (Decimal("5.2"), Decimal("8800")),
        (Decimal("20.00"), Decimal("8800")),
        (Decimal("20.01"), Decimal("6600")),
        (Decimal("100.00"), Decimal("6600")),
    ],
)
def test_selects_explicit_sqm_rate_at_each_approved_boundary(strategy, sqm_rates, metric, price):
    assert strategy.select_rate(sqm_rates, PlotterBillingMetric.SQM, metric).unit_price == price


def test_calculates_billable_sqm_for_the_whole_job_with_a_one_sqm_minimum(strategy):
    assert strategy.billable_sqm(Decimal("50"), Decimal("50"), 1) == Decimal("1")
    assert strategy.billable_sqm(Decimal("200"), Decimal("150"), 2) == Decimal("6")


def test_uses_job_quantity_for_quantity_billed_items(strategy):
    rate = PlotterRate(
        Decimal("1"), Decimal("200"), PlotterBillingMetric.JOB_QUANTITY, Decimal("400")
    )
    assert strategy.calculate_amount([rate], quantity=12) == Decimal("4800")


def test_rejects_catalog_records_with_mixed_billing_metrics(strategy):
    rates = [
        PlotterRate(Decimal("1"), Decimal("5"), PlotterBillingMetric.SQM, Decimal("1000")),
        PlotterRate(
            Decimal("1"), Decimal("200"), PlotterBillingMetric.JOB_QUANTITY, Decimal("100")
        ),
    ]
    with pytest.raises(ValueError, match="mixed billing metrics"):
        strategy.calculate_amount(
            rates, quantity=1, width_cm=Decimal("100"), height_cm=Decimal("100")
        )


@pytest.mark.parametrize("metric", [Decimal("5.005"), Decimal("100.01")])
def test_reports_a_missing_rate_for_gaps_and_areas_over_one_hundred(strategy, sqm_rates, metric):
    with pytest.raises(MissingPlotterRateError):
        strategy.select_rate(sqm_rates, PlotterBillingMetric.SQM, metric)


def test_reports_a_missing_rate_when_an_explicit_catalog_cell_is_empty(strategy):
    only_first_range = [
        PlotterRate(Decimal("1"), Decimal("5"), PlotterBillingMetric.SQM, Decimal("9000"))
    ]
    with pytest.raises(MissingPlotterRateError):
        strategy.select_rate(only_first_range, PlotterBillingMetric.SQM, Decimal("6"))
