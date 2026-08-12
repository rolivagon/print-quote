"""Plotter catalog rates with decimal boundaries and billing metrics."""

from decimal import Decimal

from sqlmodel import Field, SQLModel

from quote.domain.enums import PlotterBillingMetric


class PlotterPricing(SQLModel, table=True):
    """An explicit net-CLP rate for either a Plotter substrate or finish."""

    __tablename__ = "plotter_pricing"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int | None = Field(default=None, foreign_key="papers.id", index=True)
    finish_id: int | None = Field(default=None, foreign_key="finishes.id", index=True)
    billing_metric: PlotterBillingMetric
    minimum: Decimal = Field(decimal_places=2, max_digits=10)
    maximum: Decimal = Field(decimal_places=2, max_digits=10)
    unit_price: Decimal = Field(decimal_places=2, max_digits=12)
    currency: str = Field(default="CLP", max_length=3)
