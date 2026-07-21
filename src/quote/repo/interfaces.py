"""Repository interfaces."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from quote.domain.enums import FinishType, Unit, UserRole
from quote.domain.models import FixedProduct as FixedProductDomain
from quote.domain.models import Quote

if TYPE_CHECKING:
    from quote.repo.models import FixedProductQuantityRange

if TYPE_CHECKING:
    from quote.repo.models import Client, Finish, Paper, User


class QuoteRepository(ABC):
    """Abstract repository for quotes."""

    @abstractmethod
    def save(self, quote: Quote) -> Quote:
        """Save a quote."""
        pass

    @abstractmethod
    def get_by_id(self, quote_id: str) -> Quote | None:
        """Get a quote by ID."""
        pass


class DigitalPriceRepository(ABC):
    """Repository for digital printing price tables."""

    @abstractmethod
    def get_price_table_by_color_config(self, color_config: str) -> list[tuple[int, int, Decimal]]:
        """Get price table by color configuration.

        Returns:
            List of tuples (min_qty, max_qty, price_per_sheet)
        """
        pass

    @abstractmethod
    def get_diploma_price(self) -> Decimal:
        """Get special price for diploma format."""
        pass

    @abstractmethod
    def get_finishing_prices(self) -> dict[str, dict[str, Any]]:
        """Get finishing prices with mode and price."""
        pass


class PlotterPriceRepository(ABC):
    """Repository for plotter printing price tables."""

    @abstractmethod
    def get_material_prices(self) -> dict[str, Decimal]:
        """Get material prices per square meter."""
        pass

    @abstractmethod
    def get_finishing_prices(self) -> dict[str, dict[str, Any]]:
        """Get finishing prices with mode and price."""
        pass

    @abstractmethod
    def get_minimum_charge_sqm(self) -> Decimal:
        """Get minimum chargeable square meters."""
        pass


class OffsetPriceRepository(ABC):
    """Repository for offset printing price tables."""

    @abstractmethod
    def get_plates_price_per_color(self) -> Decimal:
        """Get price per color for plates."""
        pass

    @abstractmethod
    def get_run_price_table(self) -> dict[int, Decimal]:
        """Get run prices by quantity."""
        pass

    @abstractmethod
    def get_finishing_price_table(self, finishing_type: str) -> dict[int, Decimal]:
        """Get finishing prices by quantity for specific finishing type."""
        pass

    @abstractmethod
    def get_fixed_costs(self) -> dict[str, Decimal]:
        """Get fixed costs like molds, setup fees, etc."""
        pass

    @abstractmethod
    def get_merma_per_design(self) -> int:
        """Get merma (waste) sheets per design."""
        pass


class GeometryRepository(ABC):
    """Repository for geometry and packing parameters."""

    @abstractmethod
    def get_default_geometry(self) -> dict[str, Any]:
        """Get default geometry parameters."""
        pass

    @abstractmethod
    def get_standard_sheet_sizes(self) -> dict[str, dict[str, float]]:
        """Get standard sheet sizes for each print type."""
        pass


class FinancialRulesRepository(ABC):
    """Repository for financial rules and configurations."""

    @abstractmethod
    def get_vat_rate(self) -> Decimal:
        """Get VAT/IVA rate."""
        pass

    @abstractmethod
    def get_markup_rates(self) -> dict[str, Decimal]:
        """Get markup rates by print category."""
        pass

    @abstractmethod
    def get_rounding_mode(self) -> str:
        """Get rounding mode (hundreds, tens, units)."""
        pass


class FixedProductRepository(ABC):
    """Repository for fixed products with quantity-based pricing."""

    @abstractmethod
    def create(
        self,
        product_id: str,
        name: str,
        print_type: str,
        base_quote_snapshot: dict,
        client_id: int | None = None,
    ) -> "FixedProduct":
        """Create a new fixed product without ranges.

        Args:
            product_id: Unique product identifier
            name: Product display name
            print_type: Print type (DIGITAL, OFFSET, PLOTTER)
            base_quote_snapshot: JSON snapshot of base quote
            client_id: Client ID if client-specific, None for global

        Returns:
            Created FixedProduct instance
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_uuid(self, uuid: str) -> "FixedProduct | None":
        """Get a fixed product by UUID.

        Args:
            uuid: Product UUID

        Returns:
            FixedProduct if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_product_id(self, product_id: str) -> "FixedProduct | None":
        """Get a fixed product by product_id (slug).

        Args:
            product_id: Unique product identifier

        Returns:
            FixedProduct if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(
        self, client_id: int | None = None, include_globals: bool = True
    ) -> "list[FixedProduct]":
        """List all fixed products.

        Args:
            client_id: Filter by client_id (optional)
            include_globals: Include global products (client_id=None)

        Returns:
            List of fixed products
        """
        raise NotImplementedError

    @abstractmethod
    def add_range(
        self,
        product_uuid: str,
        min_quantity: int,
        max_quantity: int,
        unit_price: Decimal,
    ) -> "FixedProductQuantityRange":
        """Add a quantity range to a fixed product.

        Args:
            product_uuid: Product UUID
            min_quantity: Minimum quantity (inclusive)
            max_quantity: Maximum quantity (inclusive)
            unit_price: Price per unit for this range

        Returns:
            Created FixedProductQuantityRange

        Raises:
            ValueError: If range overlaps with existing ranges
        """
        raise NotImplementedError

    @abstractmethod
    def update_range(
        self,
        range_id: str,
        min_quantity: int | None = None,
        max_quantity: int | None = None,
        unit_price: Decimal | None = None,
    ) -> "FixedProductQuantityRange | None":
        """Update a quantity range.

        Args:
            range_id: Range UUID
            min_quantity: New min quantity (optional)
            max_quantity: New max quantity (optional)
            unit_price: New unit price (optional)

        Returns:
            Updated range if found, None otherwise

        Raises:
            ValueError: If updated range overlaps with other ranges
        """
        raise NotImplementedError

    @abstractmethod
    def to_domain(self, product: "FixedProduct") -> "FixedProductDomain":
        """Convert SQL model to domain model.

        Args:
            product: SQL FixedProduct model

        Returns:
            Domain FixedProduct model
        """
        raise NotImplementedError

    @abstractmethod
    def delete_range(self, range_id: str) -> bool:
        """Delete a quantity range.

        Args:
            range_id: Range UUID

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, product_uuid: str) -> bool:
        """Delete a fixed product and all its ranges.

        Args:
            product_uuid: Product UUID

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError

    @abstractmethod
    def check_range_overlap(
        self, product_uuid: str, min_qty: int, max_qty: int, exclude_range_id: str | None = None
    ) -> bool:
        """Check if a range overlaps with existing ranges.

        Args:
            product_uuid: Product UUID
            min_qty: Minimum quantity to check
            max_qty: Maximum quantity to check
            exclude_range_id: Optional range ID to exclude from check (for updates)

        Returns:
            True if overlap exists, False otherwise
        """
        raise NotImplementedError


class UserRepository(ABC):
    """Repository for User (Seller) operations with soft delete."""

    @abstractmethod
    def create(self, name: str, email: str) -> "User":
        """Create a new user.

        Args:
            name: User's full name
            email: User's unique email address

        Returns:
            Created User instance

        Raises:
            ValueError: If email already exists
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> "User | None":
        """Get user by ID.

        Args:
            user_id: User's primary key
            include_deleted: If True, include soft-deleted users

        Returns:
            User if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str, include_deleted: bool = False) -> "User | None":
        """Get user by email address.

        Args:
            email: User's email address
            include_deleted: If True, include soft-deleted users

        Returns:
            User if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, include_deleted: bool = False) -> "list[User]":
        """List all users.

        Args:
            include_deleted: If True, include soft-deleted users

        Returns:
            List of users ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        user_id: UUID,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role: UserRole | None = None,
        commit: bool = True,
    ) -> "User | None":
        """Update user information.

        Args:
            user_id: User's primary key
            name: New name (optional)
            email: New email (optional)
            is_active: New active status (optional)

        Returns:
            Updated User if found, None otherwise

        Raises:
            ValueError: If new email already exists
        """
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user by setting deleted_at timestamp.

        Args:
            user_id: User's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        raise NotImplementedError

    @abstractmethod
    def restore(self, user_id: UUID) -> bool:
        """Restore a soft-deleted user.

        Args:
            user_id: User's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        raise NotImplementedError


class ClientRepository(ABC):
    """Repository for Client operations with soft delete."""

    @abstractmethod
    def create_individual(
        self,
        tax_id: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> "Client":
        """Create a new individual client.

        Args:
            tax_id: Tax/RUT identifier
            first_name: First name
            last_name: Last name
            email: Email address (optional)
            phone: Phone number (optional)
            address: Physical address (optional)

        Returns:
            Created Client instance

        Raises:
            ValueError: If tax_id already exists
        """
        raise NotImplementedError

    @abstractmethod
    def create_company(
        self,
        tax_id: str,
        company_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> "Client":
        """Create a new company client.

        Args:
            tax_id: Tax/RUT identifier
            company_name: Company name
            email: Email address (optional)
            phone: Phone number (optional)
            address: Physical address (optional)

        Returns:
            Created Client instance

        Raises:
            ValueError: If tax_id already exists
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, client_id: int, include_deleted: bool = False) -> "Client | None":
        """Get client by ID.

        Args:
            client_id: Client's primary key
            include_deleted: If True, include soft-deleted clients

        Returns:
            Client if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_tax_id(self, tax_id: str, include_deleted: bool = False) -> "Client | None":
        """Get client by tax ID.

        Args:
            tax_id: Tax/RUT identifier
            include_deleted: If True, include soft-deleted clients

        Returns:
            Client if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, include_deleted: bool = False) -> "list[Client]":
        """List all clients.

        Args:
            include_deleted: If True, include soft-deleted clients

        Returns:
            List of clients ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        client_id: int,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None,
    ) -> "Client | None":
        """Update client information.

        Args:
            client_id: Client's primary key
            email: New email (optional)
            phone: New phone (optional)
            address: New address (optional)
            first_name: New first name for individuals (optional)
            last_name: New last name for individuals (optional)
            company_name: New company name for companies (optional)

        Returns:
            Updated Client if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, client_id: int) -> bool:
        """Soft delete a client by setting deleted_at timestamp.

        Args:
            client_id: Client's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        raise NotImplementedError

    @abstractmethod
    def restore(self, client_id: int) -> bool:
        """Restore a soft-deleted client.

        Args:
            client_id: Client's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        raise NotImplementedError


class PaperRepository(ABC):
    """Repository for Paper master data with soft delete."""

    @abstractmethod
    def create(
        self,
        name: str,
        weight: int,
        description: str | None = None,
    ) -> "Paper":
        """Create a new paper.

        Args:
            name: Paper name (e.g., "Couche 300g")
            weight: Paper weight in grams
            description: Optional description

        Returns:
            Created Paper instance

        Raises:
            ValueError: If name already exists
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, paper_id: int, include_deleted: bool = False) -> "Paper | None":
        """Get paper by ID.

        Args:
            paper_id: Paper's primary key
            include_deleted: If True, include soft-deleted papers

        Returns:
            Paper if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str, include_deleted: bool = False) -> "Paper | None":
        """Get paper by name.

        Args:
            name: Paper name
            include_deleted: If True, include soft-deleted papers

        Returns:
            Paper if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, include_deleted: bool = False) -> "list[Paper]":
        """List all papers.

        Args:
            include_deleted: If True, include soft-deleted papers

        Returns:
            List of papers ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> "list[Paper]":
        """List only active (non-deleted and is_active=True) papers.

        Returns:
            List of active papers ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        paper_id: int,
        name: str | None = None,
        weight: int | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> "Paper | None":
        """Update paper information.

        Args:
            paper_id: Paper's primary key
            name: New name (optional)
            weight: New weight (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated Paper if found, None otherwise

        Raises:
            ValueError: If new name already exists
        """
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, paper_id: int) -> bool:
        """Soft delete a paper by setting deleted_at timestamp.

        Args:
            paper_id: Paper's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        raise NotImplementedError

    @abstractmethod
    def restore(self, paper_id: int) -> bool:
        """Restore a soft-deleted paper.

        Args:
            paper_id: Paper's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        raise NotImplementedError


class FinishRepository(ABC):
    """Repository for Finish master data with soft delete."""

    @abstractmethod
    def create(
        self,
        name: str,
        finish_type: FinishType,
        unit: Unit,
        description: str | None = None,
    ) -> "Finish":
        """Create a new finish.

        Args:
            name: Finish name (e.g., "Corte Recto")
            finish_type: Type of finish (CUT, TROQUEL, etc.)
            unit: Unit of measurement (JOB, PER_ITEM, etc.)
            description: Optional description

        Returns:
            Created Finish instance

        Raises:
            ValueError: If name already exists
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, finish_id: int, include_deleted: bool = False) -> "Finish | None":
        """Get finish by ID.

        Args:
            finish_id: Finish's primary key
            include_deleted: If True, include soft-deleted finishes

        Returns:
            Finish if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str, include_deleted: bool = False) -> "Finish | None":
        """Get finish by name.

        Args:
            name: Finish name
            include_deleted: If True, include soft-deleted finishes

        Returns:
            Finish if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, include_deleted: bool = False) -> "list[Finish]":
        """List all finishes.

        Args:
            include_deleted: If True, include soft-deleted finishes

        Returns:
            List of finishes ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> "list[Finish]":
        """List only active (non-deleted and is_active=True) finishes.

        Returns:
            List of active finishes ordered by name
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        finish_id: int,
        name: str | None = None,
        finish_type: FinishType | None = None,
        unit: Unit | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> "Finish | None":
        """Update finish information.

        Args:
            finish_id: Finish's primary key
            name: New name (optional)
            finish_type: New finish type (optional)
            unit: New unit (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated Finish if found, None otherwise

        Raises:
            ValueError: If new name already exists
        """
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, finish_id: int) -> bool:
        """Soft delete a finish by setting deleted_at timestamp.

        Args:
            finish_id: Finish's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        raise NotImplementedError

    @abstractmethod
    def restore(self, finish_id: int) -> bool:
        """Restore a soft-deleted finish.

        Args:
            finish_id: Finish's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        raise NotImplementedError
