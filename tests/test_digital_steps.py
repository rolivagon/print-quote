"""Tests for digital printing step-by-step calculations (TDD approach)."""

from decimal import Decimal

from quote.domain.enums import PrintType
from quote.pricing.digital import DigitalPricingStrategy
from quote.pricing.packing import PackingCalculator


class TestDigital500Flyers:
    """Test 500 Flyers digital 4/0 case step by step."""

    def test_step_1_pieces_per_sheet(self, flyer_500_case, default_geometry, standard_sizes):
        """Step 1: Calculate pieces per sheet = 9."""
        calculator = PackingCalculator()
        case = flyer_500_case

        pieces_per_sheet = calculator.calculate_pieces_per_sheet(
            piece_width_cm=case["width_cm"],
            piece_height_cm=case["height_cm"],
            sheet_width_cm=standard_sizes["digital_sheet"]["usable_width_cm"],
            sheet_height_cm=standard_sizes["digital_sheet"]["usable_height_cm"],
            bleed_mm=default_geometry["bleed_mm"],
            margin_mm=default_geometry["margin_mm"],
            gap_mm=default_geometry["gap_mm"],
            allow_rotate=default_geometry["allow_rotate"],
        )

        assert pieces_per_sheet == case["expected"]["pieces_per_sheet"], (
            f"Expected {case['expected']['pieces_per_sheet']} pieces per sheet, got {pieces_per_sheet}"
        )

    def test_step_2_sheets_needed(self, flyer_500_case):
        """Step 2: Calculate sheets needed = ceil(500/9) = 56."""
        calculator = PackingCalculator()
        case = flyer_500_case

        sheets = calculator.calculate_sheets_needed(
            quantity=case["quantity"], pieces_per_sheet=case["expected"]["pieces_per_sheet"]
        )

        assert sheets == case["expected"]["sheets_needed"], (
            f"Expected {case['expected']['sheets_needed']} sheets, got {sheets}"
        )

    def test_step_3_sheet_cost_calculation(self, flyer_500_case, digital_price_table):
        """Step 3: Calculate sheet cost = 56 * $715 = $40.040."""
        strategy = DigitalPricingStrategy()
        case = flyer_500_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        assert sheet_cost == case["expected"]["sheet_cost"], (
            f"Expected sheet cost {case['expected']['sheet_cost']}, got {sheet_cost}"
        )

    def test_step_4_finishing_cost(self, flyer_500_case, digital_finishing_prices):
        """Step 4: Calculate finishing cost = $3.000."""
        strategy = DigitalPricingStrategy()
        case = flyer_500_case

        finishing_cost = strategy.calculate_finishing_cost(
            finishing_type=case["finishing"],
            quantity=case["quantity"],
            finishing_prices=digital_finishing_prices,
        )

        assert finishing_cost == case["expected"]["finishing_cost"], (
            f"Expected finishing cost {case['expected']['finishing_cost']}, got {finishing_cost}"
        )

    def test_step_5_subtotal_before_markup(
        self, flyer_500_case, digital_price_table, digital_finishing_prices
    ):
        """Step 5: Calculate subtotal before markup = $43.040."""
        strategy = DigitalPricingStrategy()
        case = flyer_500_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        finishing_cost = strategy.calculate_finishing_cost(
            finishing_type=case["finishing"],
            quantity=case["quantity"],
            finishing_prices=digital_finishing_prices,
        )

        subtotal = sheet_cost + finishing_cost

        assert subtotal == case["expected"]["subtotal_before_markup"], (
            f"Expected subtotal {case['expected']['subtotal_before_markup']}, got {subtotal}"
        )

    def test_step_6_apply_markup(self, flyer_500_case, financial_rules):
        """Step 6: Apply 0% markup = $43.040."""
        strategy = DigitalPricingStrategy()
        case = flyer_500_case

        subtotal = case["expected"]["subtotal_before_markup"]
        markup_rate = financial_rules["markup_by_category"][PrintType.DIGITAL]

        with_markup = strategy.apply_markup(subtotal, markup_rate)

        assert with_markup == case["expected"]["total_with_markup"], (
            f"Expected with markup {case['expected']['total_with_markup']}, got {with_markup}"
        )

    def test_step_7_apply_iva_and_rounding(self, flyer_500_case, financial_rules):
        """Step 7: Apply IVA and round to hundreds = $51.200."""
        strategy = DigitalPricingStrategy()
        case = flyer_500_case

        with_markup = case["expected"]["total_with_markup"]
        iva_rate = financial_rules["vat_rate"]

        with_iva = strategy.apply_iva(with_markup, iva_rate)
        final_total = strategy.round_to_hundreds(with_iva)
        final_net = strategy.round_to_hundreds(with_markup)

        assert final_total == case["expected"]["total_final"], (
            f"Expected final total {case['expected']['total_final']}, got {final_total}"
        )
        assert final_net == case["expected"]["net_before_vat"], (
            f"Expected net before VAT {case['expected']['net_before_vat']}, got {final_net}"
        )


class TestDigital20Diplomas:
    """Test 20 Diplomas digital 4/0 case step by step."""

    def test_step_1_pieces_per_sheet(self, diploma_20_case, default_geometry, standard_sizes):
        """Step 1: Calculate pieces per sheet = 2 (approximate)."""
        calculator = PackingCalculator()
        case = diploma_20_case

        pieces_per_sheet = calculator.calculate_pieces_per_sheet(
            piece_width_cm=case["width_cm"],
            piece_height_cm=case["height_cm"],
            sheet_width_cm=standard_sizes["digital_sheet"]["usable_width_cm"],
            sheet_height_cm=standard_sizes["digital_sheet"]["usable_height_cm"],
            bleed_mm=default_geometry["bleed_mm"],
            margin_mm=default_geometry["margin_mm"],
            gap_mm=default_geometry["gap_mm"],
            allow_rotate=default_geometry["allow_rotate"],
        )

        assert pieces_per_sheet == case["expected"]["pieces_per_sheet"], (
            f"Expected {case['expected']['pieces_per_sheet']} pieces per sheet, got {pieces_per_sheet}"
        )

    def test_step_2_sheets_needed(self, diploma_20_case):
        """Step 2: Calculate sheets needed = 10."""
        calculator = PackingCalculator()
        case = diploma_20_case

        sheets = calculator.calculate_sheets_needed(
            quantity=case["quantity"], pieces_per_sheet=case["expected"]["pieces_per_sheet"]
        )

        assert sheets == case["expected"]["sheets_needed"], (
            f"Expected {case['expected']['sheets_needed']} sheets, got {sheets}"
        )

    def test_step_3_sheet_cost_with_special_price(self, diploma_20_case, digital_price_table):
        """Step 3: Calculate sheet cost with special diploma price = $17.600."""
        strategy = DigitalPricingStrategy()
        case = diploma_20_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        assert sheet_cost == case["expected"]["sheet_cost"], (
            f"Expected sheet cost {case['expected']['sheet_cost']}, got {sheet_cost}"
        )

    def test_step_4_subtotal_calculation(
        self, diploma_20_case, digital_price_table, digital_finishing_prices
    ):
        """Step 4: Calculate subtotal = $20.600."""
        strategy = DigitalPricingStrategy()
        case = diploma_20_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        finishing_cost = (
            strategy.calculate_finishing_cost(
                finishing_type=case["finishing"],
                quantity=case["quantity"],
                finishing_prices=digital_finishing_prices,
            )
            if case["finishing"]
            else Decimal("0")
        )

        subtotal = sheet_cost + finishing_cost

        assert subtotal == case["expected"]["subtotal_before_markup"], (
            f"Expected subtotal {case['expected']['subtotal_before_markup']}, got {subtotal}"
        )


class TestDigital300Tarjetas:
    """Test 300 Tarjetas digital 4/4 case step by step."""

    def test_step_1_pieces_per_sheet(self, tarjeta_300_case, default_geometry, standard_sizes):
        """Step 1: Calculate pieces per sheet = 21."""
        calculator = PackingCalculator()
        case = tarjeta_300_case

        pieces_per_sheet = calculator.calculate_pieces_per_sheet(
            piece_width_cm=case["width_cm"],
            piece_height_cm=case["height_cm"],
            sheet_width_cm=standard_sizes["digital_sheet"]["usable_width_cm"],
            sheet_height_cm=standard_sizes["digital_sheet"]["usable_height_cm"],
            bleed_mm=default_geometry["bleed_mm"],
            margin_mm=default_geometry["margin_mm"],
            gap_mm=default_geometry["gap_mm"],
            allow_rotate=default_geometry["allow_rotate"],
        )

        assert pieces_per_sheet == case["expected"]["pieces_per_sheet"], (
            f"Expected {case['expected']['pieces_per_sheet']} pieces per sheet, got {pieces_per_sheet}"
        )

    def test_step_2_sheets_needed(self, tarjeta_300_case):
        """Step 2: Calculate sheets needed = ceil(300/21) = 15."""
        calculator = PackingCalculator()
        case = tarjeta_300_case

        sheets = calculator.calculate_sheets_needed(
            quantity=case["quantity"], pieces_per_sheet=case["expected"]["pieces_per_sheet"]
        )

        assert sheets == case["expected"]["sheets_needed"], (
            f"Expected {case['expected']['sheets_needed']} sheets, got {sheets}"
        )

    def test_step_3_sheet_cost_4_4_color(self, tarjeta_300_case, digital_price_table):
        """Step 3: Calculate sheet cost for 4/4 = 15 * $2.090 = $31.350."""
        strategy = DigitalPricingStrategy()
        case = tarjeta_300_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        assert sheet_cost == case["expected"]["sheet_cost"], (
            f"Expected sheet cost {case['expected']['sheet_cost']}, got {sheet_cost}"
        )

    def test_step_4_subtotal_calculation(
        self, tarjeta_300_case, digital_price_table, digital_finishing_prices
    ):
        """Step 4: Calculate subtotal = $34.350."""
        strategy = DigitalPricingStrategy()
        case = tarjeta_300_case

        sheet_cost = strategy.calculate_sheet_cost(
            sheets=case["expected"]["sheets_needed"],
            color_config=case["color_config"],
            price_table=digital_price_table,
        )

        finishing_cost = strategy.calculate_finishing_cost(
            finishing_type=case["finishing"],
            quantity=case["quantity"],
            finishing_prices=digital_finishing_prices,
        )

        subtotal = sheet_cost + finishing_cost

        assert subtotal == case["expected"]["subtotal_before_markup"], (
            f"Expected subtotal {case['expected']['subtotal_before_markup']}, got {subtotal}"
        )


class TestDigitalPricingHelpers:
    """Test helper methods for digital pricing calculations."""

    def test_price_lookup_by_quantity(self, digital_price_table):
        """Test price lookup based on quantity ranges."""
        strategy = DigitalPricingStrategy()

        # Test 4/0 price lookup
        price_56_sheets = strategy.lookup_price_by_quantity(56, digital_price_table["4/0"])
        assert price_56_sheets == Decimal("715"), (
            f"Expected 715 for 56 sheets, got {price_56_sheets}"
        )

        # Test 4/4 price lookup
        price_15_sheets = strategy.lookup_price_by_quantity(15, digital_price_table["4/4"])
        assert price_15_sheets == Decimal("2090"), (
            f"Expected 2090 for 15 sheets, got {price_15_sheets}"
        )

    def test_markup_calculation(self):
        """Test markup calculation."""
        strategy = DigitalPricingStrategy()

        base_amount = Decimal("43040")
        markup_rate = Decimal("0.50")  # 50%

        result = strategy.apply_markup(base_amount, markup_rate)
        expected = base_amount * (1 + markup_rate)  # 43040 * 1.5 = 64560

        assert result == expected, f"Expected {expected}, got {result}"

    def test_iva_calculation(self):
        """Test IVA calculation."""
        strategy = DigitalPricingStrategy()

        net_amount = Decimal("64560")
        iva_rate = Decimal("0.19")  # 19%

        result = strategy.apply_iva(net_amount, iva_rate)
        expected = net_amount * (1 + iva_rate)  # 64560 * 1.19 = 76826.40

        assert result == expected, f"Expected {expected}, got {result}"

    def test_rounding_to_hundreds(self):
        """Test rounding to nearest hundred."""
        strategy = DigitalPricingStrategy()

        # Test cases for rounding
        test_cases = [
            (Decimal("76826.40"), Decimal("76800")),  # rounds down
            (Decimal("76850"), Decimal("76900")),  # rounds up
            (Decimal("76800"), Decimal("76800")),  # exact hundred
            (Decimal("64560"), Decimal("64600")),  # rounds up
        ]

        for input_val, expected in test_cases:
            result = strategy.round_to_hundreds(input_val)
            assert result == expected, f"Expected {expected} for {input_val}, got {result}"
