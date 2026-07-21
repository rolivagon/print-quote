"""Money and currency handling utilities."""

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel


class Money(BaseModel):
    """Money value object."""

    amount: Decimal
    currency: str = "CLP"

    def __str__(self) -> str:
        """String representation of money."""
        return f"${self.amount:,.0f}".replace(",", ".")


def apply_markup(amount: Decimal, rate: Decimal) -> Decimal:
    """Apply markup rate to base amount.

    Args:
        amount: Base amount
        rate: Markup rate (e.g., 0.50 for 50%)

    Returns:
        Amount with markup applied
    """
    return amount * (Decimal("1") + rate)


def apply_vat(amount: Decimal, vat_rate: Decimal) -> Decimal:
    """Apply VAT/IVA to net amount.

    Args:
        amount: Net amount
        vat_rate: VAT rate (e.g., 0.19 for 19%)

    Returns:
        Amount with VAT applied
    """
    return amount * (Decimal("1") + vat_rate)


def round_money(amount: Decimal, mode: str = "hundreds") -> Decimal:
    """Round money amount according to specified mode.

    Args:
        amount: Amount to round
        mode: Rounding mode ("hundreds", "tens", "units")

    Returns:
        Rounded amount
    """
    if mode == "hundreds":
        # Round to nearest 100
        return (amount / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(
            "100"
        )
    elif mode == "tens":
        # Round to nearest 10
        return (amount / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal(
            "10"
        )
    elif mode == "units":
        # Round to nearest unit
        return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    else:
        raise ValueError(f"Unknown rounding mode: {mode}")


def calculate_markup_amount(base_amount: Decimal, markup_rate: Decimal) -> Decimal:
    """Calculate just the markup amount.

    Args:
        base_amount: Base amount
        markup_rate: Markup rate (e.g., 0.50 for 50%)

    Returns:
        Markup amount only
    """
    return base_amount * markup_rate


def calculate_vat_amount(net_amount: Decimal, vat_rate: Decimal) -> Decimal:
    """Calculate just the VAT amount.

    Args:
        net_amount: Net amount
        vat_rate: VAT rate (e.g., 0.19 for 19%)

    Returns:
        VAT amount only
    """
    return net_amount * vat_rate
