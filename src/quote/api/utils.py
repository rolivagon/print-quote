"""Utility functions for API formatting."""

from decimal import Decimal


def format_clp(amount: Decimal) -> str:
    """Format amount to Chilean Peso (CLP) string.

    Format: $1.234.567,89
    - Thousands separator: . (dot)
    - Decimal separator: , (comma)
    - Currency symbol: $

    Args:
        amount: Decimal amount to format

    Returns:
        Formatted CLP string
    """
    int_part = int(amount)
    decimal_part = amount - Decimal(int_part)

    # Format integer part with dots as thousands separator
    int_str = f"{int_part:,}".replace(",", ".")

    # Format decimal part with comma
    if decimal_part > 0:
        dec_str = f",{int(decimal_part * 100):02d}"
    else:
        dec_str = ""

    return f"${int_str}{dec_str}"
