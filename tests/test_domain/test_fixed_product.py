"""Tests for Fixed Product domain models (TDD)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from quote.domain.enums import PrintType
from quote.domain.models import FixedProduct, QuantityRange, QuoteBreakdown


class TestQuantityRange:
    """Test QuantityRange model validation."""

    def test_valid_quantity_range(self):
        """Should create valid quantity range."""
        range_qty = QuantityRange(min_qty=1, max_qty=10, unit_price=Decimal("1000"))
        assert range_qty.min_qty == 1
        assert range_qty.max_qty == 10
        assert range_qty.unit_price == Decimal("1000")

    def test_quantity_range_without_max(self):
        """Should allow None for max_qty (unlimited)."""
        range_qty = QuantityRange(min_qty=100, max_qty=None, unit_price=Decimal("500"))
        assert range_qty.min_qty == 100
        assert range_qty.max_qty is None

    def test_invalid_min_qty_zero(self):
        """Should reject min_qty = 0."""
        with pytest.raises(ValidationError):
            QuantityRange(min_qty=0, max_qty=10, unit_price=Decimal("1000"))

    def test_invalid_negative_unit_price(self):
        """Should reject negative unit_price."""
        with pytest.raises(ValidationError):
            QuantityRange(min_qty=1, max_qty=10, unit_price=Decimal("-100"))

    def test_invalid_zero_unit_price(self):
        """Should reject zero unit_price."""
        with pytest.raises(ValidationError):
            QuantityRange(min_qty=1, max_qty=10, unit_price=Decimal("0"))


class TestFixedProduct:
    """Test FixedProduct model."""

    @pytest.fixture
    def sample_breakdown(self):
        """Create a sample QuoteBreakdown for testing."""
        return QuoteBreakdown(
            print_type=PrintType.DIGITAL,
            quantity=100,
            dimensions={"width_mm": 800.0, "height_mm": 2000.0},
            pieces_per_sheet=2,
            sheets_needed=50,
            total_sheets_with_merma=55,
            material_cost=Decimal("50000"),
            finishing_cost=Decimal("5000"),
            subtotal_before_markup=Decimal("55000"),
            markup_applied=Decimal("27500"),
            subtotal_with_markup=Decimal("82500"),
            net_before_iva=Decimal("82500"),
            iva_amount=Decimal("15675"),
            total_final=Decimal("98175"),
        )

    def test_create_fixed_product(self, sample_breakdown):
        """Should create fixed product with valid data."""
        product = FixedProduct(
            id="roller-80x200",
            name="Roller 80x200",
            base_quote=sample_breakdown,
            quantity_ranges=[
                QuantityRange(min_qty=1, max_qty=3, unit_price=Decimal("38500")),
                QuantityRange(min_qty=4, max_qty=6, unit_price=Decimal("34100")),
            ],
            print_type=PrintType.DIGITAL,
        )
        assert product.id == "roller-80x200"
        assert product.name == "Roller 80x200"
        assert len(product.quantity_ranges) == 2
        assert product.print_type == PrintType.DIGITAL
        assert product.client_id is None  # Global by default

    def test_create_fixed_product_with_client(self, sample_breakdown):
        """Should create client-specific fixed product."""
        product = FixedProduct(
            id="client-product-1",
            name="Client Special Product",
            base_quote=sample_breakdown,
            quantity_ranges=[QuantityRange(min_qty=1, max_qty=100, unit_price=Decimal("1000"))],
            print_type=PrintType.DIGITAL,
            client_id="client-123",
        )
        assert product.client_id == "client-123"

    def test_fixed_product_empty_ranges(self, sample_breakdown):
        """Should allow empty quantity_ranges (created without ranges initially)."""
        product = FixedProduct(
            id="empty-product",
            name="Product Without Ranges",
            base_quote=sample_breakdown,
            quantity_ranges=[],  # Empty initially
            print_type=PrintType.DIGITAL,
        )
        assert len(product.quantity_ranges) == 0


class TestRangeOverlapValidation:
    """Test range overlap validation logic."""

    def test_ranges_do_not_overlap(self):
        """Should not detect overlap for non-overlapping ranges."""
        ranges = [
            QuantityRange(min_qty=1, max_qty=10, unit_price=Decimal("100")),
            QuantityRange(min_qty=11, max_qty=20, unit_price=Decimal("90")),
            QuantityRange(min_qty=21, max_qty=None, unit_price=Decimal("80")),
        ]
        # Helper function to check overlap (will be implemented in service)
        has_overlap = check_ranges_overlap(ranges)
        assert has_overlap is False

    def test_ranges_overlap_adjacent(self):
        """Should detect overlap for adjacent ranges (10 and 11 overlap)."""
        ranges = [
            QuantityRange(min_qty=1, max_qty=10, unit_price=Decimal("100")),
            QuantityRange(min_qty=10, max_qty=20, unit_price=Decimal("90")),  # Overlaps at 10
        ]
        has_overlap = check_ranges_overlap(ranges)
        assert has_overlap is True

    def test_ranges_overlap_nested(self):
        """Should detect overlap for nested ranges."""
        ranges = [
            QuantityRange(min_qty=1, max_qty=100, unit_price=Decimal("100")),
            QuantityRange(min_qty=50, max_qty=60, unit_price=Decimal("90")),  # Nested
        ]
        has_overlap = check_ranges_overlap(ranges)
        assert has_overlap is True


# Helper function (will be moved to appropriate module)
def check_ranges_overlap(ranges: list[QuantityRange]) -> bool:
    """Check if any ranges overlap.

    Two ranges overlap if they share any quantity values.
    Range A (min_a, max_a) overlaps with Range B (min_b, max_b) if:
    - min_a <= max_b AND min_b <= max_a (inclusive)
    - None (unlimited) is treated as infinity
    """
    for i, range_a in enumerate(ranges):
        for range_b in ranges[i + 1 :]:
            min_a, max_a = range_a.min_qty, range_a.max_qty
            min_b, max_b = range_b.min_qty, range_b.max_qty

            # Treat None as infinity for comparison
            max_a_val = float("inf") if max_a is None else max_a
            max_b_val = float("inf") if max_b is None else max_b

            # Check overlap: A starts before B ends AND B starts before A ends
            if min_a <= max_b_val and min_b <= max_a_val:
                return True
    return False
