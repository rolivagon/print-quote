"""Application lifespan contracts."""

import asyncio

from quote.api import main


class _Connection:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_: object) -> None:
        return None


class _Engine:
    def __init__(self) -> None:
        self.connected = False

    def connect(self) -> _Connection:
        self.connected = True
        return _Connection()


def test_lifespan_checks_postgresql_connectivity(monkeypatch) -> None:
    engine = _Engine()
    monkeypatch.setattr(main, "configure_database", lambda: engine)

    async def start_application() -> None:
        async with main.lifespan(main.app):
            pass

    asyncio.run(start_application())

    assert engine.connected
