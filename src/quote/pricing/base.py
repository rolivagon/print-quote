"""Base pricing classes and interfaces."""

from abc import ABC, abstractmethod

from quote.domain.models import Item, QuoteBreakdown


class PricingStrategy(ABC):
    """Abstract base class for pricing strategies."""

    @abstractmethod
    def calculate_price(self) -> float:
        """Calculate price for the given parameters."""
        pass


class PricingEngine(ABC):
    """Abstract base class for pricing engines."""

    @abstractmethod
    def price(self, item: Item) -> QuoteBreakdown:
        """Calculate complete price breakdown for an item."""
        raise NotImplementedError("Subclasses must implement price method")
