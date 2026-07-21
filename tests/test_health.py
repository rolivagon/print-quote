"""Health endpoint contract."""

from quote.api.main import health


def test_health_reports_ready() -> None:
    assert health() == {"status": "ok"}
