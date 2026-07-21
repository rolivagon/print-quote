"""Client model."""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from quote.domain.enums import ClientType


class Client(SQLModel, table=True):
    """Client model supporting both individuals and companies."""

    __tablename__ = "clients"

    id: int | None = Field(default=None, primary_key=True)
    client_type: ClientType
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    tax_id: str = Field(index=True, description="RUT/NIT/ID fiscal")

    # Individual fields
    first_name: str | None = None
    last_name: str | None = None

    # Company fields
    company_name: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    deleted_at: datetime | None = Field(default=None, index=True)

    # Creator tracking
    created_by_id: UUID | None = Field(default=None, foreign_key="users.id")

    # Relationships
    quotes: list["Quote"] = Relationship(back_populates="client")  # noqa: F821
    created_by: "User" = Relationship(back_populates="clients")  # noqa: F821
    fixed_products: list["FixedProduct"] = Relationship(back_populates="client")  # noqa: F821
