"""Tests for quote service integration (TDD approach)."""

from decimal import Decimal

import pytest

from quote.domain.enums import PrintType
from quote.domain.models import QuoteBreakdown


class TestQuoteServiceDigitalIntegration:
    """Test quote service integration for digital printing."""

    def test_digital_500_flyers_complete_quote(
        self,
        quote_service,
        flyer_500_case,
        digital_price_table,
        digital_finishing_prices,
        default_geometry,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for 500 flyers digital case."""
        case = flyer_500_case

        quote_breakdown = quote_service.generate_digital_quote(
            quantity=case["quantity"],
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            paper_spec=case.get("paper_spec", "couche_300g"),
            color_config=case["color_config"],
            finishing_type=case["finishing"],
            price_table=digital_price_table,
            finishing_prices=digital_finishing_prices,
            geometry=default_geometry,
            sheet_config=standard_sizes["digital_sheet"],
            financial_rules=financial_rules,
        )

        # Verify all components match expected values
        assert quote_breakdown.pieces_per_sheet == case["expected"]["pieces_per_sheet"]
        assert quote_breakdown.sheets_needed == case["expected"]["sheets_needed"]
        assert quote_breakdown.material_cost == case["expected"]["sheet_cost"]
        assert quote_breakdown.finishing_cost == case["expected"]["finishing_cost"]
        assert quote_breakdown.subtotal_before_markup == case["expected"]["subtotal_before_markup"]
        assert (
            quote_breakdown.markup_applied
            == case["expected"]["total_with_markup"] - case["expected"]["subtotal_before_markup"]
        )
        assert quote_breakdown.subtotal_with_markup == case["expected"]["total_with_markup"]
        assert quote_breakdown.total_final == case["expected"]["total_final"]
        assert quote_breakdown.net_before_iva == case["expected"]["net_before_vat"]
        assert quote_breakdown.print_type == PrintType.DIGITAL

    def test_digital_20_diplomas_complete_quote(
        self,
        quote_service,
        diploma_20_case,
        digital_diploma_price,
        digital_finishing_prices,
        default_geometry,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for 20 diplomas digital case."""
        case = diploma_20_case

        quote_breakdown = quote_service.generate_digital_diploma_quote(
            quantity=case["quantity"],
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            paper_spec=case.get("paper_spec", "couche_300g"),
            color_config=case["color_config"],
            finishing_type=case["finishing"],
            diploma_price=digital_diploma_price,
            finishing_prices=digital_finishing_prices,
            geometry=default_geometry,
            sheet_config=standard_sizes["digital_sheet"],
            financial_rules=financial_rules,
        )

        # Verify key components
        assert quote_breakdown.pieces_per_sheet == case["expected"]["pieces_per_sheet"]
        assert quote_breakdown.sheets_needed == case["expected"]["sheets_needed"]
        assert quote_breakdown.material_cost == case["expected"]["sheet_cost"]
        assert quote_breakdown.subtotal_before_markup == case["expected"]["subtotal_before_markup"]
        assert quote_breakdown.print_type == PrintType.DIGITAL

    def test_digital_300_tarjetas_complete_quote(
        self,
        quote_service,
        tarjeta_300_case,
        digital_price_table,
        digital_finishing_prices,
        default_geometry,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for 300 tarjetas digital case."""
        case = tarjeta_300_case

        quote_breakdown = quote_service.generate_digital_quote(
            quantity=case["quantity"],
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            paper_spec=case.get("paper_spec", "couche_300g"),
            color_config=case["color_config"],
            finishing_type=case["finishing"],
            price_table=digital_price_table,
            finishing_prices=digital_finishing_prices,
            geometry=default_geometry,
            sheet_config=standard_sizes["digital_sheet"],
            financial_rules=financial_rules,
        )

        # Verify key components
        assert quote_breakdown.pieces_per_sheet == case["expected"]["pieces_per_sheet"]
        assert quote_breakdown.sheets_needed == case["expected"]["sheets_needed"]
        assert quote_breakdown.material_cost == case["expected"]["sheet_cost"]
        assert quote_breakdown.subtotal_before_markup == case["expected"]["subtotal_before_markup"]
        assert quote_breakdown.print_type == PrintType.DIGITAL


class TestQuoteServicePlotterIntegration:
    """Test quote service integration for plotter printing."""

    def test_plotter_afiche_70x50_complete_quote(
        self,
        quote_service,
        afiche_plotter_case,
        plotter_price_table,
        plotter_finishing_prices,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for afiche plotter case."""
        case = afiche_plotter_case

        quote_breakdown = quote_service.generate_plotter_quote(
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            material_type=case["material"],
            finishing_type=case["finishing"],
            price_table=plotter_price_table,
            finishing_prices=plotter_finishing_prices,
            minimum_m2=standard_sizes["plotter_minimum_m2"],
            financial_rules=financial_rules,
        )

        # Verify components
        assert quote_breakdown.square_meters == case["expected"]["m2"]
        assert quote_breakdown.material_cost == case["expected"]["material_cost"]
        assert quote_breakdown.finishing_cost == case["expected"]["finishing_cost"]
        assert quote_breakdown.subtotal_before_markup == case["expected"]["subtotal_before_markup"]
        assert quote_breakdown.print_type == PrintType.PLOTTER

    def test_plotter_lona_300x100_complete_quote(
        self,
        quote_service,
        lona_plotter_case,
        plotter_price_table,
        plotter_finishing_prices,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for lona plotter case with multiple finishings."""
        case = lona_plotter_case

        quote_breakdown = quote_service.generate_plotter_quote_with_multiple_finishings(
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            material_type=case["material"],
            finishing_list=case["terminaciones"],
            price_table=plotter_price_table,
            finishing_prices=plotter_finishing_prices,
            minimum_m2=standard_sizes["plotter_minimum_m2"],
            financial_rules=financial_rules,
        )

        # Verify components
        assert quote_breakdown.square_meters == case["expected"]["m2"]
        assert quote_breakdown.material_cost == case["expected"]["material_cost"]
        assert quote_breakdown.print_type == PrintType.PLOTTER


class TestQuoteServiceOffsetIntegration:
    """Test quote service integration for offset printing."""

    def test_offset_5000_units_complete_quote(
        self,
        quote_service,
        offset_5000_case,
        offset_price_table,
        default_geometry,
        standard_sizes,
        financial_rules,
    ):
        """Test complete quote generation for 5000 units offset case."""
        case = offset_5000_case

        quote_breakdown = quote_service.generate_offset_quote(
            quantity=case["cantidad"],
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            paper_spec="couche_300g",  # assumed
            color_config=case["color"],
            finishing_type=case["terminacion"],
            price_table=offset_price_table,
            geometry=default_geometry,
            sheet_config=standard_sizes["offset_sheet"],
            merma_per_design=case["expected"]["merma_hojas"],
            num_designs=1,
            financial_rules=financial_rules,
        )

        # Verify all major components
        assert quote_breakdown.pieces_per_sheet == case["expected"]["pieces_per_sheet"]
        assert quote_breakdown.total_sheets_with_merma == 5300  # 5000 + 300
        assert quote_breakdown.plates_cost == case["expected"]["planchas_costo"]
        assert quote_breakdown.run_cost == case["expected"]["tiraje_costo"]
        assert quote_breakdown.finishing_cost == case["expected"]["terminacion_costo"]
        assert quote_breakdown.fixed_costs == case["expected"]["molde_costo"]
        assert quote_breakdown.subtotal_before_markup == case["expected"]["subtotal_antes_markup"]
        assert quote_breakdown.markup_applied == case["expected"]["markup_0_pct"]
        assert quote_breakdown.subtotal_with_markup == case["expected"]["subtotal_con_markup"]
        assert quote_breakdown.total_final == case["expected"]["total_final"]
        assert quote_breakdown.print_type == PrintType.OFFSET

    def test_offset_quote_cost_breakdown_completeness(
        self,
        quote_service,
        offset_5000_case,
        offset_price_table,
        default_geometry,
        standard_sizes,
        financial_rules,
    ):
        """Test that offset quote breakdown includes all cost components."""
        case = offset_5000_case

        quote_breakdown = quote_service.generate_offset_quote(
            quantity=case["cantidad"],
            width_cm=case["width_cm"],
            height_cm=case["height_cm"],
            paper_spec="couche_300g",
            color_config=case["color"],
            finishing_type=case["terminacion"],
            price_table=offset_price_table,
            geometry=default_geometry,
            sheet_config=standard_sizes["offset_sheet"],
            merma_per_design=case["expected"]["merma_hojas"],
            num_designs=1,
            financial_rules=financial_rules,
        )

        # Verify all cost components are present and positive
        assert quote_breakdown.plates_cost > 0, "Plates cost should be positive"
        assert quote_breakdown.run_cost > 0, "Run cost should be positive"
        assert quote_breakdown.finishing_cost > 0, "Finishing cost should be positive"
        assert quote_breakdown.fixed_costs > 0, "Fixed costs should be positive"
        assert quote_breakdown.paper_cost > 0, "Paper cost should be positive"

        # Verify total adds up correctly
        total_calculated = (
            quote_breakdown.plates_cost
            + quote_breakdown.run_cost
            + quote_breakdown.finishing_cost
            + quote_breakdown.fixed_costs
            + quote_breakdown.paper_cost
        )

        assert total_calculated == quote_breakdown.subtotal_before_markup, (
            f"Cost components should sum to subtotal: {total_calculated} vs {quote_breakdown.subtotal_before_markup}"
        )


class TestQuoteServiceGlobalRulesApplication:
    """Test that global financial rules are applied consistently across all print types."""

    def test_markup_rates_by_print_type(self, quote_service, financial_rules):
        """Test that correct markup rates are applied by print type."""
        service = quote_service

        # Test Digital markup (0%)
        digital_markup = service.get_markup_rate_for_print_type(PrintType.DIGITAL, financial_rules)
        assert digital_markup == financial_rules["markup_by_category"][PrintType.DIGITAL]

        # Test Plotter markup (0%)
        plotter_markup = service.get_markup_rate_for_print_type(PrintType.PLOTTER, financial_rules)
        assert plotter_markup == financial_rules["markup_by_category"][PrintType.PLOTTER]

        # Test Offset markup (0%)
        offset_markup = service.get_markup_rate_for_print_type(PrintType.OFFSET, financial_rules)
        assert offset_markup == financial_rules["markup_by_category"][PrintType.OFFSET]

    def test_iva_application_consistency(self, quote_service, financial_rules):
        """Test that IVA is applied consistently across all print types."""
        service = quote_service
        vat_rate = financial_rules["vat_rate"]

        test_amounts = [Decimal("1000"), Decimal("5000"), Decimal("10000")]

        for amount in test_amounts:
            with_vat = service.apply_iva(amount, vat_rate)
            expected = amount * (1 + vat_rate)
            assert with_vat == expected, (
                f"VAT calculation mismatch for {amount}: expected {expected}, got {with_vat}"
            )

    def test_rounding_to_hundreds_consistency(self, quote_service):
        """Test that rounding to hundreds is consistent."""
        service = quote_service

        test_cases = [
            (Decimal("1234.56"), Decimal("1200")),
            (Decimal("1250.00"), Decimal("1300")),
            (Decimal("1249.99"), Decimal("1200")),
            (Decimal("1299.99"), Decimal("1300")),
        ]

        for input_amount, expected in test_cases:
            result = service.round_to_hundreds(input_amount)
            assert result == expected, (
                f"Rounding mismatch for {input_amount}: expected {expected}, got {result}"
            )


class TestQuoteBreakdownModel:
    """Test QuoteBreakdown model creation and validation."""

    def test_quote_breakdown_creation_digital(self, flyer_500_case):
        """Test creating QuoteBreakdown for digital print type."""
        case = flyer_500_case

        breakdown = QuoteBreakdown(
            print_type=PrintType.DIGITAL,
            quantity=case["quantity"],
            pieces_per_sheet=case["expected"]["pieces_per_sheet"],
            sheets_needed=case["expected"]["sheets_needed"],
            material_cost=case["expected"]["sheet_cost"],
            finishing_cost=case["expected"]["finishing_cost"],
            subtotal_before_markup=case["expected"]["subtotal_before_markup"],
            markup_applied=case["expected"]["total_with_markup"]
            - case["expected"]["subtotal_before_markup"],
            subtotal_with_markup=case["expected"]["total_with_markup"],
            iva_amount=case["expected"]["total_final"] - case["expected"]["net_before_vat"],
            total_final=case["expected"]["total_final"],
            net_before_iva=case["expected"]["net_before_vat"],
        )

        assert breakdown.print_type == PrintType.DIGITAL
        assert breakdown.quantity == case["quantity"]
        assert breakdown.total_final == case["expected"]["total_final"]

    def test_quote_breakdown_creation_offset(self, offset_5000_case):
        """Test creating QuoteBreakdown for offset print type."""
        case = offset_5000_case

        breakdown = QuoteBreakdown(
            print_type=PrintType.OFFSET,
            quantity=case["cantidad"],
            pieces_per_sheet=case["expected"]["pieces_per_sheet"],
            total_sheets_with_merma=5300,
            plates_cost=case["expected"]["planchas_costo"],
            run_cost=case["expected"]["tiraje_costo"],
            finishing_cost=case["expected"]["terminacion_costo"],
            fixed_costs=case["expected"]["molde_costo"],
            paper_cost=Decimal("800000"),  # calculated difference
            subtotal_before_markup=case["expected"]["subtotal_antes_markup"],
            markup_applied=case["expected"]["markup_0_pct"],
            subtotal_with_markup=case["expected"]["subtotal_con_markup"],
            total_final=case["expected"]["total_final"],
        )

        assert breakdown.print_type == PrintType.OFFSET
        assert breakdown.quantity == case["cantidad"]
        assert breakdown.total_final == case["expected"]["total_final"]

    def test_quote_breakdown_validation_rules(self):
        """Test QuoteBreakdown validation rules."""
        # Test that positive values are required
        with pytest.raises(ValueError):
            QuoteBreakdown(
                print_type=PrintType.DIGITAL,
                quantity=0,  # Should be positive
                total_final=Decimal("1000"),
            )

        with pytest.raises(ValueError):
            QuoteBreakdown(
                print_type=PrintType.DIGITAL,
                quantity=100,
                total_final=Decimal("-100"),  # Should be positive
            )

    def test_quote_breakdown_currency_formatting(self, flyer_500_case):
        """Test QuoteBreakdown currency formatting methods."""
        case = flyer_500_case

        breakdown = QuoteBreakdown(
            print_type=PrintType.DIGITAL,
            quantity=case["quantity"],
            total_final=case["expected"]["total_final"],
        )

        formatted_total = breakdown.format_currency(breakdown.total_final)
        assert "$" in formatted_total, "Formatted currency should include $ sign"
        assert "51.200" in formatted_total or "51,200" in formatted_total, (
            "Formatted currency should include the amount"
        )
