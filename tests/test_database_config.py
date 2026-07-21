"""Runtime database configuration tests."""

import pytest

from quote.repo.database import DatabaseConfigurationError, database_url_from_environment


def test_database_url_is_required_outside_tests(monkeypatch):
    """The application must not silently select SQLite at runtime."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL is required"):
        database_url_from_environment()


@pytest.mark.parametrize(
    "url", ["sqlite:///print_quote.db", "mysql://localhost/quotes", "not-a-url"]
)
def test_database_url_must_be_postgresql(monkeypatch, url):
    """Only PostgreSQL-compatible URLs are valid runtime configuration."""
    monkeypatch.setenv("DATABASE_URL", url)

    with pytest.raises(DatabaseConfigurationError, match="PostgreSQL-compatible"):
        database_url_from_environment()
