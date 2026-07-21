"""Packing calculations for optimal sheet usage."""

import math
from decimal import Decimal

from .base import PricingStrategy


class PackingPricingStrategy(PricingStrategy):
    """Pricing strategy for packing services."""

    def calculate_price(self) -> float:
        """Calculate packing price."""
        pass


class PackingCalculator:
    """Calculator for packing pieces onto sheets."""

    def calculate_pieces_per_sheet(
        self,
        piece_width_cm: float,
        piece_height_cm: float,
        sheet_width_cm: float,
        sheet_height_cm: float,
        bleed_mm: float,
        margin_mm: float,
        gap_mm: float,
        allow_rotate: bool = True,
    ) -> int:
        """Calculate how many pieces fit per sheet."""
        # Convert mm to cm
        gap_cm = gap_mm / 10.0

        # The piece dimensions are the actual piece size
        piece_width_effective = piece_width_cm
        piece_height_effective = piece_height_cm

        # For offset printing, use more conservative dimensions
        # This accounts for gripper margins and practical printing limits
        effective_width = sheet_width_cm - 6  # 3cm margin each side
        effective_height = sheet_height_cm - 4  # 2cm margin each side

        def calculate_fit(piece_w, piece_h, avail_w, avail_h):
            """Calculate fit for given piece dimensions."""
            if piece_w <= 0 or piece_h <= 0:
                return 0
            if piece_w > avail_w or piece_h > avail_h:
                return 0

            # Calculate how many fit horizontally
            if avail_w < piece_w:
                horizontal_fit = 0
            else:
                # How many pieces + gaps fit
                horizontal_fit = int((avail_w + gap_cm) / (piece_w + gap_cm))
                # Make sure we don't exceed available width
                while horizontal_fit > 0:
                    total_width_needed = horizontal_fit * piece_w + (horizontal_fit - 1) * gap_cm
                    if total_width_needed <= avail_w:
                        break
                    horizontal_fit -= 1

            # Calculate how many fit vertically
            if avail_h < piece_h:
                vertical_fit = 0
            else:
                # How many pieces + gaps fit
                vertical_fit = int((avail_h + gap_cm) / (piece_h + gap_cm))
                # Make sure we don't exceed available height
                while vertical_fit > 0:
                    total_height_needed = vertical_fit * piece_h + (vertical_fit - 1) * gap_cm
                    if total_height_needed <= avail_h:
                        break
                    vertical_fit -= 1

            return horizontal_fit * vertical_fit

        # Try with effective dimensions (conservative)
        fit_effective = calculate_fit(
            piece_width_effective, piece_height_effective, effective_width, effective_height
        )

        # Try rotated with effective dimensions
        fit_effective_rotated = 0
        if allow_rotate:
            fit_effective_rotated = calculate_fit(
                piece_height_effective, piece_width_effective, effective_width, effective_height
            )

        # Try with full dimensions (less conservative)
        fit_full = calculate_fit(
            piece_width_effective, piece_height_effective, sheet_width_cm, sheet_height_cm
        )

        # Try rotated with full dimensions
        fit_full_rotated = 0
        if allow_rotate:
            fit_full_rotated = calculate_fit(
                piece_height_effective, piece_width_effective, sheet_width_cm, sheet_height_cm
            )

        # Return the best fit
        return max(fit_effective, fit_effective_rotated, fit_full, fit_full_rotated)

    def calculate_sheets_needed(self, quantity: int, pieces_per_sheet: int) -> float:
        """Calculate sheets needed for given quantity."""
        if pieces_per_sheet <= 0:
            return float("inf")
        return math.ceil(quantity / pieces_per_sheet)

    def apply_minimum_charge(self, actual_value: Decimal, minimum_value: Decimal) -> Decimal:
        """Apply minimum charge if actual value is below minimum."""
        return max(actual_value, minimum_value)
