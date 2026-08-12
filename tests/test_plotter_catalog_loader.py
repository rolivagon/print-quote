"""Tests for the approved, explicit Plotter catalog definition."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from catalog_loader import existing_paper  # noqa: E402
from load_plotter_data import _catalog  # noqa: E402

from quote.domain.enums import PlotterBillingMetric  # noqa: E402
from quote.repo.models import Finish, Paper, PlotterPricing  # noqa: E402


def test_plotter_loader_rejects_an_existing_catalog_name_with_the_wrong_weight():
    class Result:
        def scalars(self):
            return self

        def first(self):
            return Paper(name="SINTÉTICO", weight=200)

    class Session:
        def execute(self, _statement):
            return Result()

    try:
        existing_paper(Session(), Paper(name="SINTÉTICO", weight=1), required_weight=1)
    except ValueError as error:
        assert "weight 1" in str(error)
    else:
        raise AssertionError("expected the conflicting weight to be rejected")


def test_plotter_catalog_contains_only_the_transcribed_explicit_net_clp_cells():
    records = _catalog().records
    papers = [record for record in records if isinstance(record, Paper)]
    finishes = [record for record in records if isinstance(record, Finish)]
    prices = [record for record in records if isinstance(record, PlotterPricing)]

    assert len(papers) == 17
    assert len(finishes) == 8
    assert {paper.weight for paper in papers} == {1}
    assert len(prices) == 67
    assert all(price.unit_price > Decimal("0") for price in prices)
    assert all(price.currency == "CLP" for price in prices)

    troquelado = next(finish for finish in finishes if finish.name == "TROQUELADO")
    troquelado_rates = [price for price in prices if price.finish_id == troquelado.id]
    assert [(rate.minimum, rate.maximum, rate.unit_price) for rate in troquelado_rates] == [
        (Decimal("1.00"), Decimal("5.00"), Decimal("9000"))
    ]

    ojetillos = next(
        finish
        for finish in finishes
        if finish.name == "OJETILLOS C/U UN ITEM PARA PONER CUANTAS LLEVA POR LIENZO"
    )
    ojetillos_rates = [price for price in prices if price.finish_id == ojetillos.id]
    assert [(rate.minimum, rate.maximum, rate.billing_metric) for rate in ojetillos_rates] == [
        (Decimal("1"), Decimal("200"), PlotterBillingMetric.JOB_QUANTITY),
        (Decimal("201"), Decimal("400"), PlotterBillingMetric.JOB_QUANTITY),
    ]
