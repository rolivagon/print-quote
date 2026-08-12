"""Add the approved explicit Plotter catalog to the configured PostgreSQL database."""

from decimal import Decimal

from catalog_loader import CatalogCollector, existing_finish, existing_paper
from sqlalchemy import select, text

from quote.domain.enums import PlotterBillingMetric
from quote.repo.database import SessionLocal, configure_database
from quote.repo.models import Finish, Paper, PlotterPricing

SQM_RANGES = [("1.00", "5.00"), ("5.01", "20.00"), ("20.01", "100.00")]
QUANTITY_RANGES = [("1", "200"), ("201", "400"), ("401", "1000")]

SUBSTRATES = [
    ("ADHESIVO PVC BRILLANTE O MATE", (11000, 8800, 6600)),
    ("ADHESIVO TRANSPARENTE", (13100, 9900, 7700)),
    ("ADHESIVO DORADO / PLATEADO", (18000, 15900, 12500)),
    ("ADHESIVO HOLOGRAFICO", (18000, 15900, 12500)),
    ("SINTÉTICO", (10000, 8000, 7000)),
    ("TELA PVC", (7000, 6000, 7000)),
    ("FLOORGRAPHIC", (27000, 25000, 22000)),
    ("CANVAS/PAPEL MURAL", (18000, 18000, 15000)),
    ("ADHESIVO PVC + IMAN", (25000, 23000, 18000)),
    ("ADHESIVO PVC + SINTRA / UNA CARA", (46000, 43000, 38000)),
    ("ADHESIVO PVC + FOAM / UNA CARA", (35000, 31000, 28000)),
    ("ADHESIVO EFECTO ESPEJO", (17000, 14000, 11500)),
    ("ADHESIVO + ACRILICO", (75000, 70000, 65000)),
    ("ADHESIVO + MDF / UNA CARA", (46000, 43000, 38000)),
    ("ADHESIVO PVC + SINTRA / DOS CARAS", (55000, 50000, 45000)),
    ("ADHESIVO PVC + FOAM / DOS CARAS", (42000, 38000, 35000)),
    ("ADHESIVO + MDF / DOS CARAS", (55000, 50000, 45000)),
]

SQM_FINISHES = [
    ("LACA UV POR M2", (8000, 6500, 5500)),
    ("TROQUELADO", (9000, None, None)),
    ("CORTE LASER SIMPLE", (1200, None, None)),
    ("CORTE LIENZOS / PENDONES", (1000, 700, None)),
    ("BOLSILLO LIENZO + HILO + TAPONES", (4500, None, None)),
]

QUANTITY_FINISHES = [
    ("OJETILLOS C/U UN ITEM PARA PONER CUANTAS LLEVA POR LIENZO", (400, 400, None)),
    ("CORTE RECTO PRODUCTOS CHICOS", (50, 30, 25)),
    ("CORTE RECTO AFICHES", (300, 200, 100)),
]


def _add_rates(
    collector: CatalogCollector,
    owner_field: str,
    owner_id: int,
    metric: PlotterBillingMetric,
    ranges: list[tuple[str, str]],
    prices: tuple[int | None, int | None, int | None],
) -> None:
    for (minimum, maximum), price in zip(ranges, prices, strict=True):
        if price is not None:
            collector.add(
                PlotterPricing(
                    **{owner_field: owner_id},
                    billing_metric=metric,
                    minimum=Decimal(minimum),
                    maximum=Decimal(maximum),
                    unit_price=Decimal(price),
                )
            )


def _catalog() -> CatalogCollector:
    """Build exactly the approved explicit Plotter data without database writes."""
    collector = CatalogCollector()
    for name, prices in SUBSTRATES:
        paper = Paper(name=name, weight=1, description="Plotter substrate", is_active=True)
        collector.add(paper)
        collector.flush()
        _add_rates(collector, "paper_id", paper.id, PlotterBillingMetric.SQM, SQM_RANGES, prices)
    for name, prices in SQM_FINISHES:
        finish = Finish(name=name, description="Plotter finish charged per m²", is_active=True)
        collector.add(finish)
        collector.flush()
        _add_rates(collector, "finish_id", finish.id, PlotterBillingMetric.SQM, SQM_RANGES, prices)
    for name, prices in QUANTITY_FINISHES:
        finish = Finish(
            name=name, description="Plotter finish charged per job quantity", is_active=True
        )
        collector.add(finish)
        collector.flush()
        _add_rates(
            collector,
            "finish_id",
            finish.id,
            PlotterBillingMetric.JOB_QUANTITY,
            QUANTITY_RANGES,
            prices,
        )
    return collector


def _existing_rate(
    session, owner_field: str, owner_id: int, source: PlotterPricing
) -> PlotterPricing | None:
    owner_column = (
        PlotterPricing.paper_id if owner_field == "paper_id" else PlotterPricing.finish_id
    )
    return (
        session.execute(
            select(PlotterPricing).where(
                owner_column == owner_id,
                PlotterPricing.billing_metric == source.billing_metric,
                PlotterPricing.minimum == source.minimum,
                PlotterPricing.maximum == source.maximum,
            )
        )
        .scalars()
        .first()
    )


def _overlapping_rate(session, owner_field: str, owner_id: int, source: PlotterPricing):
    owner_column = (
        PlotterPricing.paper_id if owner_field == "paper_id" else PlotterPricing.finish_id
    )
    return (
        session.execute(
            select(PlotterPricing)
            .where(
                owner_column == owner_id,
                PlotterPricing.billing_metric == source.billing_metric,
                PlotterPricing.minimum <= source.maximum,
                PlotterPricing.maximum >= source.minimum,
            )
            .order_by(PlotterPricing.minimum)
        )
        .scalars()
        .first()
    )


def _load_plotter_data(session) -> None:
    """Load catalog into a caller-owned transaction."""
    catalog = _catalog()
    session.execute(text("select pg_advisory_xact_lock(7298456271309843)"))
    papers = {
        paper.id: existing_paper(session, paper, required_weight=1)
        for paper in catalog.records
        if isinstance(paper, Paper)
    }
    finishes = {
        finish.id: existing_finish(session, finish)
        for finish in catalog.records
        if isinstance(finish, Finish)
    }
    for rate in (record for record in catalog.records if isinstance(record, PlotterPricing)):
        owner_field, owner = (
            ("paper_id", papers[rate.paper_id])
            if rate.paper_id is not None
            else ("finish_id", finishes[rate.finish_id])
        )
        existing = _existing_rate(session, owner_field, owner.id, rate)
        if existing is None:
            if _overlapping_rate(session, owner_field, owner.id, rate) is not None:
                raise ValueError(
                    f"Plotter rate overlap for {owner_field}={owner.id}, {rate.billing_metric.value} "
                    f"{rate.minimum}-{rate.maximum}"
                )
            session.add(
                PlotterPricing(
                    **{owner_field: owner.id},
                    billing_metric=rate.billing_metric,
                    minimum=rate.minimum,
                    maximum=rate.maximum,
                    unit_price=rate.unit_price,
                )
            )
        elif existing.unit_price != rate.unit_price or existing.currency != rate.currency:
            raise ValueError(
                f"Plotter rate conflict for {owner_field}={owner.id}, {rate.billing_metric.value} "
                f"{rate.minimum}-{rate.maximum}"
            )


def load_plotter_data(session=None) -> None:
    """Add catalog data, optionally using a caller-owned transaction."""
    if session is not None:
        _load_plotter_data(session)
        return
    with SessionLocal.begin() as session:
        _load_plotter_data(session)


def main() -> None:
    """Run the additive Plotter catalog loader against DATABASE_URL."""
    configure_database()
    load_plotter_data()


if __name__ == "__main__":
    main()
