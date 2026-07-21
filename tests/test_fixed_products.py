"""Tests for Fixed Products feature (TDD approach).

This module tests the ability to:
1. Calculate a real quote (digital/offset/plotter)
2. Save that quote as a Fixed Product with quantity ranges and fixed prices
3. Use the Fixed Product to quote different quantities

Based on real products from:
- Image 2: Roller products (80x200, 90x200, 100x200)
- Image 3: Business Cards (Tarjetas de Visita)
"""

from decimal import Decimal

import pytest

from quote.domain.enums import PrintType


class TestFixedProductRoller:
    """Test Fixed Product creation and usage for Roller products."""

    def test_create_fixed_product_from_digital_roller_quote(
        self, quote_service, fixed_product_repo
    ):
        """
        Test: Calculate a real digital quote for Roller 80x200, then save as Fixed Product.

        Based on Image 2: ROLLER 80X200 SINTETICO
        - Reference quantity: 100 (for the base quote calculation)
        - Size: 80x200 cm (converting to mm: 800x2000)
        - Material: Synthetic (Sintetico)
        - Color: 4/0 (one side)
        """
        # Calculate real quote for reference quantity (100 units)
        reference_quantity = 100

        base_quote = quote_service.generate_digital_quote(
            quantity=reference_quantity,
            width_cm=80.0,
            height_cm=200.0,
            paper_spec="sintetico",
            color_config="4/0",
            finishing_type="corte_recto",
            price_table={
                "4/0": [
                    (1, 50, Decimal("1500")),
                    (51, 100, Decimal("1200")),
                    (101, float("inf"), Decimal("1000")),
                ]
            },
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("5000")}},
            geometry={"bleed_mm": 3, "margin_mm": 5, "gap_mm": 3, "allow_rotate": True},
            sheet_config={"usable_width_cm": 160, "usable_height_cm": 220},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )

        # Verify base quote has all required fields
        assert base_quote.print_type == PrintType.DIGITAL
        assert base_quote.quantity == reference_quantity
        assert base_quote.total_final > 0

        # Create Fixed Product from base quote (Step 1: without ranges)
        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        # Verify Fixed Product was created
        assert fixed_product.id == "roller-80x200-sintetico"
        assert fixed_product.name == "Roller 80x200 Sintetico"
        assert fixed_product.print_type == PrintType.DIGITAL
        assert fixed_product.base_quote.quantity == reference_quantity

    def test_quote_with_fixed_product_range_1_to_3(self, quote_service, fixed_product_repo):
        """
        Test: Quote 2 units using Fixed Product - should use range 1-3 price.

        From Image 2: Range 1-3, unit price $38.500
        Expected total: 2 × $38.500 = $77.000
        """
        # Setup: Create Fixed Product first (Step 1)
        base_quote = self._create_roller_base_quote(quote_service, 100)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        # Step 2: Add ranges
        quantity_ranges = [
            {"min_qty": 1, "max_qty": 3, "unit_price": Decimal("38500")},
            {"min_qty": 4, "max_qty": 6, "unit_price": Decimal("34100")},
            {"min_qty": 7, "max_qty": 10, "unit_price": Decimal("30800")},
            {"min_qty": 11, "max_qty": 100, "unit_price": Decimal("28600")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote 2 units
        quote = quote_service.quote_with_fixed_product(
            product_id="roller-80x200-sintetico",
            quantity=2,
        )

        # Verify: Should use range 1-3 price ($38.500 per unit)
        expected_total = Decimal("2") * Decimal("38500")
        assert quote.total_final == expected_total
        assert quote.is_fixed_product is True
        assert quote.fixed_product_id == "roller-80x200-sintetico"
        assert quote.applied_range is not None
        assert quote.applied_range["min_qty"] == 1
        assert quote.applied_range["max_qty"] == 3
        assert quote.applied_range["unit_price"] == Decimal("38500")

        # Base reference data should be preserved
        assert quote.reference_quantity == 100
        assert quote.pieces_per_sheet is not None  # From base quote
        assert quote.sheets_needed is not None

    def test_quote_with_fixed_product_range_4_to_6(self, quote_service, fixed_product_repo):
        """
        Test: Quote 5 units using Fixed Product - should use range 4-6 price.

        From Image 2: Range 4-6, unit price $34.100
        Expected total: 5 × $34.100 = $170.500
        """
        base_quote = self._create_roller_base_quote(quote_service, 100)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        quantity_ranges = [
            {"min_qty": 1, "max_qty": 3, "unit_price": Decimal("38500")},
            {"min_qty": 4, "max_qty": 6, "unit_price": Decimal("34100")},
            {"min_qty": 7, "max_qty": 10, "unit_price": Decimal("30800")},
            {"min_qty": 11, "max_qty": 100, "unit_price": Decimal("28600")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote 5 units
        quote = quote_service.quote_with_fixed_product(
            product_id="roller-80x200-sintetico",
            quantity=5,
        )

        # Verify: Should use range 4-6 price ($34.100 per unit)
        expected_total = Decimal("5") * Decimal("34100")
        assert quote.total_final == expected_total
        assert quote.applied_range["min_qty"] == 4
        assert quote.applied_range["max_qty"] == 6
        assert quote.applied_range["unit_price"] == Decimal("34100")

    def test_quote_with_fixed_product_range_11_to_100(self, quote_service, fixed_product_repo):
        """
        Test: Quote 50 units using Fixed Product - should use range 11-100 price.

        From Image 2: Range 11-100, unit price $28.600
        Expected total: 50 × $28.600 = $1.430.000
        """
        base_quote = self._create_roller_base_quote(quote_service, 100)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        quantity_ranges = [
            {"min_qty": 1, "max_qty": 3, "unit_price": Decimal("38500")},
            {"min_qty": 4, "max_qty": 6, "unit_price": Decimal("34100")},
            {"min_qty": 7, "max_qty": 10, "unit_price": Decimal("30800")},
            {"min_qty": 11, "max_qty": 100, "unit_price": Decimal("28600")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote 50 units
        quote = quote_service.quote_with_fixed_product(
            product_id="roller-80x200-sintetico",
            quantity=50,
        )

        # Verify: Should use range 11-100 price ($28.600 per unit)
        expected_total = Decimal("50") * Decimal("28600")
        assert quote.total_final == expected_total
        assert quote.applied_range["min_qty"] == 11
        assert quote.applied_range["max_qty"] == 100
        assert quote.applied_range["unit_price"] == Decimal("28600")

    def test_quote_with_fixed_product_quantity_not_in_ranges(
        self, quote_service, fixed_product_repo
    ):
        """
        Test: Quote quantity outside all ranges should raise error.
        """
        base_quote = self._create_roller_base_quote(quote_service, 100)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        quantity_ranges = [
            {"min_qty": 1, "max_qty": 3, "unit_price": Decimal("38500")},
            {"min_qty": 4, "max_qty": 6, "unit_price": Decimal("34100")},
            {"min_qty": 7, "max_qty": 10, "unit_price": Decimal("30800")},
            {"min_qty": 11, "max_qty": 100, "unit_price": Decimal("28600")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote 150 units (outside all ranges)
        with pytest.raises(ValueError, match="No price range found for quantity 150"):
            quote_service.quote_with_fixed_product(
                product_id="roller-80x200-sintetico",
                quantity=150,
            )

    def test_quote_with_fixed_product_preserves_base_breakdown(
        self, quote_service, fixed_product_repo
    ):
        """
        Test: When using Fixed Product, the base QuoteBreakdown should be preserved
        as reference (pieces_per_sheet, sheets_needed, etc.) but total comes from range.
        """
        base_quote = self._create_roller_base_quote(quote_service, 100)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="roller-80x200-sintetico",
            name="Roller 80x200 Sintetico",
            print_type=PrintType.DIGITAL,
        )

        quantity_ranges = [
            {"min_qty": 1, "max_qty": 100, "unit_price": Decimal("30000")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote different quantity
        quote = quote_service.quote_with_fixed_product(
            product_id="roller-80x200-sintetico",
            quantity=5,
        )

        # Base data should be preserved from reference quote (100 units)
        assert quote.reference_quantity == 100
        assert quote.pieces_per_sheet == base_quote.pieces_per_sheet
        assert quote.sheets_needed == base_quote.sheets_needed

        # But totals come from fixed price
        assert quote.total_final == Decimal("5") * Decimal("30000")

    def _create_roller_base_quote(self, quote_service, quantity):
        """Helper to create a base quote for Roller products."""
        return quote_service.generate_digital_quote(
            quantity=quantity,
            width_cm=80.0,
            height_cm=200.0,
            paper_spec="sintetico",
            color_config="4/0",
            finishing_type="corte_recto",
            price_table={
                "4/0": [
                    (1, 50, Decimal("1500")),
                    (51, 100, Decimal("1200")),
                    (101, float("inf"), Decimal("1000")),
                ]
            },
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("5000")}},
            geometry={"bleed_mm": 3, "margin_mm": 5, "gap_mm": 3, "allow_rotate": True},
            sheet_config={"usable_width_cm": 160, "usable_height_cm": 220},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )


class TestFixedProductBusinessCards:
    """Test Fixed Product for Business Cards (Tarjetas de Visita)."""

    def test_create_fixed_product_business_cards_couche_4_4(
        self, quote_service, fixed_product_repo
    ):
        """
        Test: Create Fixed Product from Business Cards quote.

        Based on Image 3: TARJETAS DE VISITA, COUCHÉ 300G, 4/4, POLIMATE + CORTE RECTO
        - Reference quantity: 1000 (from the table ranges)
        - Size: Standard business card (9x5.5 cm)
        - Material: Couché 300g
        - Color: 4/4 (both sides)
        - Finish: Polimate + Corte Recto
        """
        # Calculate real quote for reference
        base_quote = quote_service.generate_digital_quote(
            quantity=1000,
            width_cm=9.0,
            height_cm=5.5,
            paper_spec="couche_300g",
            color_config="4/4",
            finishing_type="corte_recto",
            price_table={
                "4/4": [
                    (1, 50, Decimal("2500")),
                    (51, 100, Decimal("2200")),
                    (101, float("inf"), Decimal("2000")),
                ]
            },
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("3000")}},
            geometry={"bleed_mm": 2, "margin_mm": 5, "gap_mm": 2, "allow_rotate": True},
            sheet_config={"usable_width_cm": 31, "usable_height_cm": 46},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )

        # Create Fixed Product (Step 1: without ranges)
        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="tarjetas-visita-couche-4-4-polimate",
            name="Tarjetas de Visita Couche 300g 4/4 Polimate",
            print_type=PrintType.DIGITAL,
        )

        assert fixed_product.id == "tarjetas-visita-couche-4-4-polimate"

    def test_quote_business_cards_range_1_to_300(self, quote_service, fixed_product_repo):
        """
        Test: Quote 250 business cards - should use range 1-300 price.

        From Image 3: Range 1-300, unit price $125 (for 4/0) or $165 (for 4/4)
        """
        base_quote = self._create_business_cards_base_quote(quote_service, 1000)

        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="tarjetas-visita-couche-4-4",
            name="Tarjetas de Visita Couche 4/4",
            print_type=PrintType.DIGITAL,
        )

        quantity_ranges = [
            {"min_qty": 1, "max_qty": 300, "unit_price": Decimal("165")},
            {"min_qty": 400, "max_qty": 500, "unit_price": Decimal("154")},
            {"min_qty": 600, "max_qty": 700, "unit_price": Decimal("132")},
            {"min_qty": 800, "max_qty": 1000, "unit_price": Decimal("121")},
        ]

        for range_data in quantity_ranges:
            fixed_product_repo.add_range(
                fixed_product.id,
                min_quantity=range_data["min_qty"],
                max_quantity=range_data["max_qty"],
                unit_price=range_data["unit_price"],
            )

        # Quote 250 cards
        quote = quote_service.quote_with_fixed_product(
            product_id="tarjetas-visita-couche-4-4",
            quantity=250,
        )

        expected_total = Decimal("250") * Decimal("165")
        assert quote.total_final == expected_total
        assert quote.applied_range["min_qty"] == 1
        assert quote.applied_range["max_qty"] == 300

    def _create_business_cards_base_quote(self, quote_service, quantity):
        """Helper to create a base quote for Business Cards."""
        return quote_service.generate_digital_quote(
            quantity=quantity,
            width_cm=9.0,
            height_cm=5.5,
            paper_spec="couche_300g",
            color_config="4/4",
            finishing_type="corte_recto",
            price_table={
                "4/4": [
                    (1, 50, Decimal("2500")),
                    (51, 100, Decimal("2200")),
                    (101, float("inf"), Decimal("2000")),
                ]
            },
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("3000")}},
            geometry={"bleed_mm": 2, "margin_mm": 5, "gap_mm": 2, "allow_rotate": True},
            sheet_config={"usable_width_cm": 31, "usable_height_cm": 46},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )


class TestFixedProductRepository:
    """Test Fixed Product repository operations."""

    def test_list_all_fixed_products(self, quote_service, fixed_product_repo):
        """Test listing all fixed products."""
        base_quote = self._create_simple_base_quote(quote_service)

        # Create multiple products
        for product_id in ["product-1", "product-2", "product-3"]:
            quote_service.create_fixed_product_from_quote(
                base_quote=base_quote,
                product_id=product_id,
                name=f"Product {product_id}",
                print_type=PrintType.DIGITAL,
            )

        products = quote_service.list_fixed_products()
        assert len(products) == 3

    def test_get_fixed_product_by_id(self, quote_service, fixed_product_repo):
        """Test retrieving a specific fixed product."""
        base_quote = self._create_simple_base_quote(quote_service)

        quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="test-product",
            name="Test Product",
            print_type=PrintType.DIGITAL,
        )

        product = quote_service.get_fixed_product("test-product")
        assert product is not None
        assert product.id == "test-product"
        assert product.name == "Test Product"

    def test_fixed_product_not_found(self, quote_service):
        """Test error when fixed product doesn't exist."""
        with pytest.raises(ValueError, match="Fixed product not found: non-existent"):
            quote_service.quote_with_fixed_product("non-existent", quantity=10)

    def _create_simple_base_quote(self, quote_service):
        """Helper to create a simple base quote."""
        return quote_service.generate_digital_quote(
            quantity=100,
            width_cm=10.0,
            height_cm=10.0,
            paper_spec="test_paper",
            color_config="4/0",
            finishing_type="corte_recto",
            price_table={"4/0": [(1, float("inf"), Decimal("1000"))]},
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("1000")}},
            geometry={"bleed_mm": 0, "margin_mm": 0, "gap_mm": 0, "allow_rotate": True},
            sheet_config={"usable_width_cm": 30, "usable_height_cm": 45},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )


class TestFixedProductClientSpecific:
    """Test client-specific fixed products."""

    def test_create_client_specific_fixed_product(self, quote_service, fixed_product_repo):
        """Test creating a fixed product for a specific client."""
        base_quote = self._create_simple_base_quote(quote_service)

        # Note: client_id should be int for SQL, but tests use str
        # For InMemory repo, it stores as str
        fixed_product = quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="client-product-1",
            name="Client Special Product",
            print_type=PrintType.DIGITAL,
            client_id=123,  # Client-specific (int for SQL compatibility)
        )

        assert fixed_product.client_id == "123"

    def test_list_fixed_products_include_globals(self, quote_service, fixed_product_repo):
        """Test listing includes global products plus client-specific."""
        base_quote = self._create_simple_base_quote(quote_service)

        # Create global product
        quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="global-product",
            name="Global Product",
            print_type=PrintType.DIGITAL,
        )

        # Create client-specific product
        quote_service.create_fixed_product_from_quote(
            base_quote=base_quote,
            product_id="client-product",
            name="Client Product",
            print_type=PrintType.DIGITAL,
            client_id=456,
        )

        # List all products for client (should include global + client-specific)
        products = quote_service.list_fixed_products(client_id=456, include_globals=True)
        assert len(products) == 2

        # List only client-specific
        client_products = quote_service.list_fixed_products(client_id=456, include_globals=False)
        assert len(client_products) == 1
        assert client_products[0].id == "client-product"

    def _create_simple_base_quote(self, quote_service):
        """Helper to create a simple base quote."""
        return quote_service.generate_digital_quote(
            quantity=100,
            width_cm=10.0,
            height_cm=10.0,
            paper_spec="test_paper",
            color_config="4/0",
            finishing_type="corte_recto",
            price_table={"4/0": [(1, float("inf"), Decimal("1000"))]},
            finishing_prices={"corte_recto": {"mode": "per_job", "price": Decimal("1000")}},
            geometry={"bleed_mm": 0, "margin_mm": 0, "gap_mm": 0, "allow_rotate": True},
            sheet_config={"usable_width_cm": 30, "usable_height_cm": 45},
            financial_rules={
                "vat_rate": Decimal("0.19"),
                "markup_by_category": {PrintType.DIGITAL: Decimal("0.50")},
            },
        )
