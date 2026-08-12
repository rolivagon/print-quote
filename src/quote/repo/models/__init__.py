"""Database models package.

All SQLModel table classes are exported here for repository composition.
"""

from sqlmodel import SQLModel

# Import all models to register them with SQLModel metadata
from quote.repo.models.base_measurement import BaseMeasurement
from quote.repo.models.client import Client
from quote.repo.models.finish import Finish
from quote.repo.models.finish_pricing import FinishPricing
from quote.repo.models.fixed_product import FixedProduct, FixedProductQuantityRange
from quote.repo.models.paper import Paper
from quote.repo.models.paper_pricing import PaperPricing
from quote.repo.models.plotter_pricing import PlotterPricing
from quote.repo.models.quote import Quote, QuoteItem, QuoteItemFinish
from quote.repo.models.user import User

# Re-export all models
__all__ = [
    # Base
    "SQLModel",
    # User
    "User",
    # Client
    "Client",
    # Masters
    "Paper",
    "PaperPricing",
    "PlotterPricing",
    "Finish",
    "FinishPricing",
    "BaseMeasurement",
    # Fixed Products
    "FixedProduct",
    "FixedProductQuantityRange",
    # Quotes
    "Quote",
    "QuoteItem",
    "QuoteItemFinish",
]
