"""User (Seller) model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from quote.domain.enums import UserRole


class User(SQLModel, table=True):
    """User (Seller) model."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    role: UserRole = Field(default=UserRole.VENDEDOR)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None, index=True)

    # Relationships
    quotes: list["Quote"] = Relationship(back_populates="seller")  # noqa: F821
    clients: list["Client"] = Relationship(back_populates="created_by")  # noqa: F821
