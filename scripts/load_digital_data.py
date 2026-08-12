"""Add the canonical digital catalog to the configured PostgreSQL database."""

from catalog_loader import CatalogCollector, existing_finish, existing_paper
from seed_digital_data import create_digital_finishes, create_digital_papers
from sqlalchemy import select, text

from quote.repo.database import SessionLocal, configure_database
from quote.repo.models import Finish, FinishPricing, Paper, PaperPricing


def _catalog() -> CatalogCollector:
    """Build the existing canonical seed definition without writing to a database."""
    collector = CatalogCollector()
    create_digital_papers(collector)
    create_digital_finishes(collector)
    return collector


def _price_exists(session, model, owner_id: int, source: PaperPricing | FinishPricing) -> bool:
    owner_column = model.paper_id if model is PaperPricing else model.finish_id
    conditions = [
        owner_column == owner_id,
        model.print_type == source.print_type,
        model.min_quantity == source.min_quantity,
    ]
    if isinstance(source, PaperPricing):
        conditions.append(
            model.color_mode.is_(None)
            if source.color_mode is None
            else model.color_mode == source.color_mode
        )
    else:
        conditions.append(model.unit == source.unit)
    conditions.append(
        model.max_quantity.is_(None)
        if source.max_quantity is None
        else model.max_quantity == source.max_quantity
    )
    return session.execute(select(model.id).where(*conditions)).first() is not None


def load_digital_data() -> None:
    """Insert missing canonical digital data while preserving every existing row."""
    catalog = _catalog()
    with SessionLocal.begin() as session:
        # Prevent simultaneous operational runs from both inserting the same missing row.
        session.execute(text("select pg_advisory_xact_lock(7298456271309842)"))
        papers = {
            paper.id: existing_paper(session, paper)
            for paper in catalog.records
            if isinstance(paper, Paper)
        }
        finishes = {
            finish.id: existing_finish(session, finish)
            for finish in catalog.records
            if isinstance(finish, Finish)
        }
        for price in catalog.records:
            if isinstance(price, PaperPricing):
                paper = papers[price.paper_id]
                if not _price_exists(session, PaperPricing, paper.id, price):
                    session.add(
                        PaperPricing(
                            paper_id=paper.id,
                            print_type=price.print_type,
                            color_mode=price.color_mode,
                            min_quantity=price.min_quantity,
                            max_quantity=price.max_quantity,
                            unit_price=price.unit_price,
                        )
                    )
            elif isinstance(price, FinishPricing):
                finish = finishes[price.finish_id]
                if not _price_exists(session, FinishPricing, finish.id, price):
                    session.add(
                        FinishPricing(
                            finish_id=finish.id,
                            print_type=price.print_type,
                            unit=price.unit,
                            min_quantity=price.min_quantity,
                            max_quantity=price.max_quantity,
                            unit_price=price.unit_price,
                        )
                    )


def main() -> None:
    """Run the additive digital catalog loader against DATABASE_URL."""
    configure_database()
    load_digital_data()


if __name__ == "__main__":
    main()
