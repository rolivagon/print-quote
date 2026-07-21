"""PostgreSQL database configuration and session management."""

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigurationError(RuntimeError):
    """Raised when the backend is not configured with PostgreSQL."""


def database_url_from_environment() -> str:
    """Return the required PostgreSQL connection URL without a SQLite fallback."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL is required and must point to PostgreSQL")

    try:
        drivername = make_url(database_url).drivername
    except ArgumentError as exc:
        raise DatabaseConfigurationError(
            "DATABASE_URL must use a PostgreSQL-compatible URL"
        ) from exc
    if not drivername.startswith("postgresql"):
        raise DatabaseConfigurationError("DATABASE_URL must use a PostgreSQL-compatible URL")
    return database_url


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create the application engine from an explicitly validated URL."""
    url = database_url or database_url_from_environment()
    connect_args = {"sslmode": "require"} if "supabase.co" in url else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


# Binding is deferred to startup so pure domain tests remain database-free.
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def configure_database() -> Engine:
    """Validate runtime configuration and bind sessions to PostgreSQL."""
    engine = create_database_engine()
    SessionLocal.configure(bind=engine)
    return engine


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as context manager.

    Yields:
        SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
