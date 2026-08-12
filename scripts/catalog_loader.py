"""Shared additive catalog-loader primitives."""

from sqlalchemy import select

from quote.repo.models import Finish, Paper


class CatalogCollector:
    """Collect catalog models while assigning temporary relationship IDs."""

    def __init__(self) -> None:
        self.records: list[object] = []
        self._next_id = -1

    def add(self, record: object) -> None:
        self.records.append(record)

    def add_all(self, records: list[object]) -> None:
        self.records.extend(records)

    def flush(self) -> None:
        for record in self.records:
            if getattr(record, "id", None) is None:
                record.id = self._next_id
                self._next_id -= 1


def existing_paper(session, source: Paper, *, required_weight: int | None = None) -> Paper:
    """Get a substrate by name or insert it without overwriting existing data."""
    paper = session.execute(select(Paper).where(Paper.name == source.name)).scalars().first()
    if paper is not None:
        if required_weight is not None and paper.weight != required_weight:
            raise ValueError(
                f"Plotter catalog substrate '{source.name}' must have weight {required_weight}"
            )
        return paper
    paper = Paper(
        name=source.name,
        weight=source.weight,
        description=source.description,
        is_active=source.is_active,
    )
    session.add(paper)
    session.flush()
    return paper


def existing_finish(session, source: Finish) -> Finish:
    """Get a finish by name or insert it without overwriting existing data."""
    finish = session.execute(select(Finish).where(Finish.name == source.name)).scalars().first()
    if finish is not None:
        return finish
    finish = Finish(
        name=source.name,
        description=source.description,
        is_active=source.is_active,
    )
    session.add(finish)
    session.flush()
    return finish
