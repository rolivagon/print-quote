"""Tests for pricing range overlap validation."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from quote.domain.enums import PrintType, Unit
from quote.repo.models import Finish, Paper
from quote.repo.sql_repo import SQLFinishRepository, SQLPaperRepository


def test_finish_pricing_duplicate_range_fails(db_session: Session):
    """Should raise ValueError when creating a duplicate pricing range for a finish."""
    repo = SQLFinishRepository(db_session)
    finish = Finish(name="Test Finish", is_active=True)
    db_session.add(finish)
    db_session.commit()

    # Create first pricing range: 1-100
    repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("3000.00"),
    )

    # Try to create exact duplicate range
    with pytest.raises(ValueError, match="Overlapping pricing range"):
        repo.create_pricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("4000.00"),
        )


def test_finish_pricing_overlap_fails(db_session: Session):
    """Should raise ValueError when creating overlapping pricing ranges for a finish."""
    repo = SQLFinishRepository(db_session)
    finish = Finish(name="Test Finish 2", is_active=True)
    db_session.add(finish)
    db_session.commit()

    # Create range: 100-200
    repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=100,
        max_quantity=200,
        unit_price=Decimal("3000.00"),
    )

    # Try to create overlapping range: 150-250
    with pytest.raises(ValueError, match="Overlapping pricing range"):
        repo.create_pricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=150,
            max_quantity=250,
            unit_price=Decimal("4000.00"),
        )


def test_finish_pricing_unlimited_overlap_fails(db_session: Session):
    """Should handle None as infinity in overlap checks."""
    repo = SQLFinishRepository(db_session)
    finish = Finish(name="Test Finish 3", is_active=True)
    db_session.add(finish)
    db_session.commit()

    # Create range: 500+ (unlimited)
    repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=500,
        max_quantity=None,
        unit_price=Decimal("3000.00"),
    )

    # Try to create range that starts after 500
    with pytest.raises(ValueError, match="Overlapping pricing range"):
        repo.create_pricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=600,
            max_quantity=700,
            unit_price=Decimal("4000.00"),
        )


def test_paper_pricing_overlap_fails(db_session: Session):
    """Should also validate paper pricing overlaps."""
    repo = SQLPaperRepository(db_session)
    paper = Paper(name="Test Paper", weight=200, is_active=True)
    db_session.add(paper)
    db_session.commit()

    # Create range: 1-1000
    repo.create_pricing(
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        min_quantity=1,
        max_quantity=1000,
        unit_price=Decimal("100.00"),
    )

    # Try to create overlapping range
    with pytest.raises(ValueError, match="Overlapping pricing range"):
        repo.create_pricing(
            paper_id=paper.id,
            print_type=PrintType.DIGITAL,
            min_quantity=500,
            max_quantity=1500,
            unit_price=Decimal("90.00"),
        )


def test_finish_pricing_update_overlap_fails(db_session: Session):
    """Should raise ValueError when updating to an overlapping range."""
    repo = SQLFinishRepository(db_session)
    finish = Finish(name="Test Finish Update", is_active=True)
    db_session.add(finish)
    db_session.commit()

    # Create two ranges: 1-100 and 101-200
    p1 = repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("10.00"),
    )
    repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=101,
        max_quantity=200,
        unit_price=Decimal("20.00"),
    )

    # Try to update first range to overlap with second: 1-150
    with pytest.raises(ValueError, match="Overlapping pricing range"):
        repo.update_pricing(pricing_id=p1.id, max_quantity=150)


def test_finish_pricing_update_no_overlap_success(db_session: Session):
    """Should allow updating non-range fields without overlap check failing."""
    repo = SQLFinishRepository(db_session)
    finish = Finish(name="Test Finish Update Success", is_active=True)
    db_session.add(finish)
    db_session.commit()

    p1 = repo.create_pricing(
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("10.00"),
    )

    # Update price only - should work
    updated = repo.update_pricing(p1.id, unit_price=Decimal("15.00"))
    assert updated.unit_price == Decimal("15.00")

    # Update range to something else non-overlapping - should work
    updated = repo.update_pricing(p1.id, min_quantity=1, max_quantity=50)
    assert updated.max_quantity == 50
