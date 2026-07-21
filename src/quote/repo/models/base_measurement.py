"""Base measurement model."""

from decimal import Decimal

from sqlmodel import Field, SQLModel


class BaseMeasurement(SQLModel, table=True):
    """Base measurements/master formats."""

    __tablename__ = "base_measurements"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Ej: A4, A3, Carta")
    width: Decimal = Field(decimal_places=2, max_digits=8)
    height: Decimal = Field(decimal_places=2, max_digits=8)
    description: str | None = None
    is_active: bool = Field(default=True)
