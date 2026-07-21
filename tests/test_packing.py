"""Tests for packing calculations with TDD approach."""

from quote.pricing.packing import PackingCalculator


class TestPackingCalculations:
    """Test packing calculations for different print types."""

    def test_digital_base_case_9_pieces_per_sheet(self, default_geometry, standard_sizes):
        """Test base case: pieza 10x15 cm en pliego 30x45 cm debe dar 9 piezas."""
        calculator = PackingCalculator()

        piece_width_cm = 10
        piece_height_cm = 15
        sheet = standard_sizes["digital_sheet"]
        geometry = default_geometry

        result = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],  # 29 cm
            sheet_height_cm=sheet["usable_height_cm"],  # 44 cm
            bleed_mm=geometry["bleed_mm"],  # 3mm
            margin_mm=geometry["margin_mm"],  # 5mm
            gap_mm=geometry["gap_mm"],  # 3mm
            allow_rotate=geometry["allow_rotate"],
        )

        assert result == 9, f"Expected 9 pieces per sheet, got {result}"

    def test_pieces_too_large_for_sheet_returns_zero(self, default_geometry, standard_sizes):
        """Test that pieces larger than usable area return 0."""
        calculator = PackingCalculator()

        # Pieza más grande que área útil (29x44 cm)
        piece_width_cm = 35
        piece_height_cm = 50
        sheet = standard_sizes["digital_sheet"]
        geometry = default_geometry

        result = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],
            sheet_height_cm=sheet["usable_height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=geometry["allow_rotate"],
        )

        assert result == 0, f"Large pieces should return 0, got {result}"

    def test_rotation_improves_fit_when_beneficial(self, default_geometry, standard_sizes):
        """Test that rotation is used when it improves the fit."""
        calculator = PackingCalculator()

        # Pieza que cabe mejor rotada: 20x8 cm
        piece_width_cm = 20
        piece_height_cm = 8
        sheet = standard_sizes["digital_sheet"]
        geometry = default_geometry

        # Con rotación permitida
        result_with_rotation = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],
            sheet_height_cm=sheet["usable_height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=True,
        )

        # Sin rotación
        result_without_rotation = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],
            sheet_height_cm=sheet["usable_height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=False,
        )

        assert result_with_rotation >= result_without_rotation, (
            f"Rotation should not decrease fit: {result_with_rotation} vs {result_without_rotation}"
        )

    def test_diploma_case_2_pieces_per_sheet(self, default_geometry, standard_sizes):
        """Test diploma case: 21,5x28 cm should fit 2 pieces per sheet."""
        calculator = PackingCalculator()

        piece_width_cm = 21.5
        piece_height_cm = 28
        sheet = standard_sizes["digital_sheet"]
        geometry = default_geometry

        result = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],
            sheet_height_cm=sheet["usable_height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=geometry["allow_rotate"],
        )

        assert result == 2, f"Diploma should fit 2 pieces per sheet, got {result}"

    def test_tarjeta_case_21_pieces_per_sheet(self, default_geometry, standard_sizes):
        """Test tarjeta case: 9,4x5,9 cm should fit 21 pieces per sheet."""
        calculator = PackingCalculator()

        piece_width_cm = 9.4
        piece_height_cm = 5.9
        sheet = standard_sizes["digital_sheet"]
        geometry = default_geometry

        result = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["usable_width_cm"],
            sheet_height_cm=sheet["usable_height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=geometry["allow_rotate"],
        )

        assert result == 21, f"Tarjetas should fit 21 pieces per sheet, got {result}"

    def test_offset_large_piece_1_per_sheet(self, default_geometry, standard_sizes):
        """Test offset case: 55x41,6 cm piece should fit 1 per sheet on 66x44 cm."""
        calculator = PackingCalculator()

        piece_width_cm = 55
        piece_height_cm = 41.6
        sheet = standard_sizes["offset_sheet"]
        geometry = default_geometry

        result = calculator.calculate_pieces_per_sheet(
            piece_width_cm=piece_width_cm,
            piece_height_cm=piece_height_cm,
            sheet_width_cm=sheet["width_cm"],  # offset usa toda la plancha
            sheet_height_cm=sheet["height_cm"],
            bleed_mm=geometry["bleed_mm"],
            margin_mm=geometry["margin_mm"],
            gap_mm=geometry["gap_mm"],
            allow_rotate=geometry["allow_rotate"],
        )

        assert result == 1, f"Large offset piece should fit 1 per sheet, got {result}"

    def test_calculate_sheets_needed(self):
        """Test calculation of sheets needed for given quantity and pieces per sheet."""
        calculator = PackingCalculator()

        # 500 piezas con 9 por pliego = 56 pliegos
        sheets = calculator.calculate_sheets_needed(quantity=500, pieces_per_sheet=9)
        assert sheets == 56, f"Expected 56 sheets for 500/9, got {sheets}"

        # 20 piezas con 2 por pliego = 10 pliegos
        sheets = calculator.calculate_sheets_needed(quantity=20, pieces_per_sheet=2)
        assert sheets == 10, f"Expected 10 sheets for 20/2, got {sheets}"

        # 300 piezas con 21 por pliego = 15 pliegos
        sheets = calculator.calculate_sheets_needed(quantity=300, pieces_per_sheet=21)
        assert sheets == 15, f"Expected 15 sheets for 300/21, got {sheets}"

    def test_zero_pieces_per_sheet_handling(self):
        """Test that zero pieces per sheet is handled gracefully."""
        calculator = PackingCalculator()

        # Should return a very large number or handle appropriately
        sheets = calculator.calculate_sheets_needed(quantity=100, pieces_per_sheet=0)
        assert sheets == float("inf") or sheets > 10000, (
            f"Should handle zero pieces per sheet gracefully, got {sheets}"
        )
