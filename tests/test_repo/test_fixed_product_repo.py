"""Tests for SQLFixedProductRepository (TDD)."""

from decimal import Decimal

import pytest

from quote.repo.sql_fixed_product_repo import SQLFixedProductRepository


class TestSQLFixedProductRepository:
    """Test SQLFixedProductRepository with real database."""

    @pytest.fixture
    def repo(self, db_session):
        """Create repository fixture."""
        return SQLFixedProductRepository(db_session)

    def test_create_fixed_product(self, repo):
        """Should create fixed product without ranges."""
        product = repo.create(
            product_id="roller-80x200",
            name="Roller 80x200",
            print_type="DIGITAL",
            base_quote_snapshot={
                "reference_quantity": 100,
                "dimensions": {"width_cm": 80.0, "height_cm": 200.0},
                "pieces_per_sheet": 2,
            },
            client_id=None,
        )

        assert product.product_id == "roller-80x200"
        assert product.name == "Roller 80x200"
        assert product.print_type == "DIGITAL"
        assert product.client_id is None
        assert product.base_quote_snapshot["pieces_per_sheet"] == 2
        assert len(product.ranges) == 0

    def test_create_fixed_product_with_client(self, repo, sample_client):
        """Should create client-specific fixed product."""
        product = repo.create(
            product_id="client-product",
            name="Client Special",
            print_type="OFFSET",
            base_quote_snapshot={"reference_quantity": 1000},
            client_id=sample_client.id,
        )

        assert product.client_id == sample_client.id

    def test_get_by_uuid(self, repo):
        """Should retrieve product by UUID."""
        created = repo.create(
            product_id="test-uuid",
            name="Test UUID",
            print_type="PLOTTER",
            base_quote_snapshot={},
        )

        retrieved = repo.get_by_uuid(str(created.id))

        assert retrieved is not None
        assert retrieved.product_id == "test-uuid"
        assert retrieved.name == "Test UUID"

    def test_get_by_product_id(self, repo):
        """Should retrieve product by product_id."""
        repo.create(
            product_id="unique-slug",
            name="By Slug",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        retrieved = repo.get_by_product_id("unique-slug")

        assert retrieved is not None
        assert retrieved.name == "By Slug"

    def test_list_all_global_products(self, repo):
        """Should list only global products."""
        # Create global products
        repo.create("global-1", "Global 1", "DIGITAL", {})
        repo.create("global-2", "Global 2", "OFFSET", {})

        products = repo.list_all(client_id=None, include_globals=True)

        assert len(products) == 2
        assert all(p.client_id is None for p in products)

    def test_add_range_to_product(self, repo):
        """Should add range to existing product."""
        product = repo.create(
            product_id="product-with-ranges",
            name="Product with Ranges",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        range_obj = repo.add_range(
            product_uuid=str(product.id),
            min_quantity=1,
            max_quantity=10,
            unit_price=Decimal("1000"),
        )

        assert range_obj.min_quantity == 1
        assert range_obj.max_quantity == 10
        assert range_obj.unit_price == Decimal("1000")
        assert range_obj.fixed_product_id == product.id

    def test_add_overlapping_range_raises_error(self, repo):
        """Should raise error when adding overlapping range."""
        product = repo.create(
            product_id="overlap-test",
            name="Overlap Test",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        # Add first range 1-10
        repo.add_range(str(product.id), 1, 10, Decimal("1000"))

        # Try to add overlapping range 5-15
        with pytest.raises(ValueError, match="overlaps with existing ranges"):
            repo.add_range(str(product.id), 5, 15, Decimal("900"))

    def test_update_range(self, repo):
        """Should update existing range."""
        product = repo.create(
            product_id="update-test",
            name="Update Test",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        range_obj = repo.add_range(str(product.id), 1, 10, Decimal("1000"))
        updated = repo.update_range(
            range_id=str(range_obj.id),
            min_quantity=1,
            max_quantity=20,
            unit_price=Decimal("900"),
        )

        assert updated.max_quantity == 20
        assert updated.unit_price == Decimal("900")

    def test_update_range_overlap_raises_error(self, repo):
        """Should raise error when update causes overlap."""
        product = repo.create(
            product_id="update-overlap",
            name="Update Overlap",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        range1 = repo.add_range(str(product.id), 1, 10, Decimal("1000"))
        repo.add_range(str(product.id), 11, 20, Decimal("900"))

        # Try to update range1 to 1-15 (overlaps with 11-20)
        with pytest.raises(ValueError, match="overlaps with existing ranges"):
            repo.update_range(
                range_id=str(range1.id),
                max_quantity=15,
            )

    def test_delete_range(self, repo):
        """Should delete range by ID."""
        product = repo.create(
            product_id="delete-range",
            name="Delete Range",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        range_obj = repo.add_range(str(product.id), 1, 10, Decimal("1000"))
        deleted = repo.delete_range(str(range_obj.id))

        assert deleted is True

        # Verify range is gone
        updated_product = repo.get_by_uuid(str(product.id))
        assert len(updated_product.ranges) == 0

    def test_delete_product_cascades_to_ranges(self, repo):
        """Should delete product and all its ranges."""
        product = repo.create(
            product_id="cascade-delete",
            name="Cascade Delete",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        repo.add_range(str(product.id), 1, 10, Decimal("1000"))
        repo.add_range(str(product.id), 11, 20, Decimal("900"))

        deleted = repo.delete(str(product.id))

        assert deleted is True

        # Verify product is gone
        assert repo.get_by_uuid(str(product.id)) is None

    def test_check_range_overlap(self, repo):
        """Should detect overlapping ranges."""
        product = repo.create(
            product_id="overlap-check",
            name="Overlap Check",
            print_type="DIGITAL",
            base_quote_snapshot={},
        )

        repo.add_range(str(product.id), 1, 10, Decimal("1000"))

        # Check overlap with 5-15 (overlaps)
        assert repo.check_range_overlap(str(product.id), 5, 15) is True

        # Check overlap with 11-20 (doesn't overlap)
        assert repo.check_range_overlap(str(product.id), 11, 20) is False

    def test_list_with_client_filter(self, repo, sample_client):
        """Should filter products by client."""
        # Create global product
        repo.create("global-prod", "Global", "DIGITAL", {})

        # Create client-specific product
        repo.create("client-prod", "Client", "OFFSET", {}, client_id=sample_client.id)

        # List only client products
        client_products = repo.list_all(client_id=sample_client.id, include_globals=False)
        assert len(client_products) == 1
        assert client_products[0].product_id == "client-prod"

        # List client + global products
        all_products = repo.list_all(client_id=sample_client.id, include_globals=True)
        assert len(all_products) == 2


@pytest.fixture
def sample_client(db_session):
    """Create a sample client for testing."""
    from quote.domain.enums import ClientType
    from quote.repo.models import Client

    client = Client(
        client_type=ClientType.INDIVIDUAL,
        tax_id="12.345.678-9",
        first_name="Test",
        last_name="Client",
        email="test@example.com",
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client
