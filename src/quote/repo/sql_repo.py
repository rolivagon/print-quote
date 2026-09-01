"""SQL repository implementations."""

from datetime import datetime
from decimal import Decimal
from unicodedata import combining, normalize
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from quote.domain.enums import ClientType, ColorMode, FinishType, PrintType, Unit, UserRole
from quote.pricing.internal_costs import validate_finish_unit, validate_paper_unit
from quote.repo.interfaces import (
    ClientRepository,
    FinishRepository,
    PaperRepository,
    UserRepository,
)
from quote.repo.models import (
    BaseMeasurement,
    Client,
    Finish,
    FinishInternalCost,
    FinishPricing,
    Paper,
    PaperInternalCost,
    PaperPricing,
    PlotterPricing,
    User,
)


class SQLMasterRepository:
    """Repository for master data (papers, finishes, measurements)."""

    def __init__(self, session: Session):
        self._session = session

    def get_paper_price(
        self, paper_id: int, print_type, quantity: int, color_mode: "ColorMode | None" = None
    ):
        """Get paper price for specific quantity, print type and color mode.

        Args:
            paper_id: ID of the paper
            print_type: Type of printing (DIGITAL, OFFSET, PLOTTER)
            quantity: Quantity to print
            color_mode: Color mode (4/0, 4/4) - only used for DIGITAL

        Returns:
            PaperPricing if found in range, None otherwise
        """
        statement = (
            select(PaperPricing)
            .where(PaperPricing.paper_id == paper_id)
            .where(PaperPricing.print_type == print_type)
            .where(PaperPricing.min_quantity <= quantity)
            .where((PaperPricing.max_quantity == None) | (PaperPricing.max_quantity >= quantity))
        )

        # Filter by color_mode if provided
        if color_mode is not None:
            statement = statement.where(
                (PaperPricing.color_mode == color_mode) | (PaperPricing.color_mode == None)
            )

        return self._session.execute(statement).scalars().first()

    def get_finish_price(self, finish_id: int, print_type, quantity: int):
        """Get finish price for specific quantity and print type.

        Args:
            finish_id: ID of the finish
            print_type: Type of printing (DIGITAL, OFFSET, PLOTTER)
            quantity: Quantity to print

        Returns:
            FinishPricing if found in range, None otherwise
        """
        from quote.repo.models import FinishPricing

        statement = (
            select(FinishPricing)
            .where(FinishPricing.finish_id == finish_id)
            .where(FinishPricing.print_type == print_type)
            .where(FinishPricing.min_quantity <= quantity)
            .where((FinishPricing.max_quantity == None) | (FinishPricing.max_quantity >= quantity))
        )
        return self._session.execute(statement).scalars().first()

    def get_all_active_papers(self) -> list[Paper]:
        """Get all active papers."""
        statement = select(Paper).where(Paper.is_active == True)
        return list(self._session.execute(statement).scalars().all())

    def get_all_active_finishes(self) -> list[Finish]:
        """Get all active finishes."""
        statement = select(Finish).where(Finish.is_active == True)
        return list(self._session.execute(statement).scalars().all())

    def get_all_base_measurements(self) -> list[BaseMeasurement]:
        """Get all base measurements."""
        statement = select(BaseMeasurement)
        return list(self._session.execute(statement).scalars().all())

    def get_plotter_rates_for_paper(self, paper_id: int) -> list[PlotterPricing]:
        """Return every explicit Plotter rate for a substrate."""
        return list(
            self._session.execute(
                select(PlotterPricing).where(PlotterPricing.paper_id == paper_id)
            ).scalars()
        )

    def get_plotter_paper_by_name(self, name: str) -> Paper | None:
        """Find a catalog substrate regardless of case or Unicode accents."""
        normalized_name = "".join(
            character for character in normalize("NFD", name.casefold()) if not combining(character)
        )
        papers = self._session.execute(
            select(Paper)
            .join(PlotterPricing, PlotterPricing.paper_id == Paper.id)
            .distinct()
            .order_by(Paper.id)
        ).scalars()
        return next(
            (
                paper
                for paper in papers
                if "".join(
                    character
                    for character in normalize("NFD", paper.name.casefold())
                    if not combining(character)
                )
                == normalized_name
            ),
            None,
        )

    def get_plotter_rates_for_finish(self, finish_id: int) -> list[PlotterPricing]:
        """Return every explicit Plotter rate for a finish."""
        return list(
            self._session.execute(
                select(PlotterPricing).where(PlotterPricing.finish_id == finish_id)
            ).scalars()
        )


class SQLUserRepository(UserRepository):
    """SQL implementation of User repository with soft delete."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        name: str,
        email: str,
        role: UserRole = UserRole.VENDEDOR,
        **_ignored: object,
    ) -> User:
        """Create a new user.

        Args:
            name: User's full name
            email: User's unique email address
            role: User role (default: VENDEDOR)

        Extra legacy arguments are ignored so repository fixtures can construct
        profiles without reintroducing a persisted credential column.

        Returns:
            Created User instance

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists (including deleted users)
        existing = self._session.execute(select(User).where(User.email == email)).scalars().first()
        if existing:
            raise ValueError(f"User with email '{email}' already exists")

        user = User(name=name, email=email, role=role, is_active=True)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        """Get user by ID.

        Args:
            user_id: User's primary key
            include_deleted: If True, include soft-deleted users

        Returns:
            User if found, None otherwise
        """
        user = self._session.get(User, user_id)
        if user and not include_deleted and user.deleted_at is not None:
            return None
        return user

    def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """Get user by email address.

        Args:
            email: User's email address
            include_deleted: If True, include soft-deleted users

        Returns:
            User if found, None otherwise
        """
        statement = select(User).where(User.email == email)
        user = self._session.execute(statement).scalars().first()
        if user and not include_deleted and user.deleted_at is not None:
            return None
        return user

    def list_all(self, include_deleted: bool = False) -> list[User]:
        """List all users.

        Args:
            include_deleted: If True, include soft-deleted users

        Returns:
            List of users ordered by name
        """
        statement = select(User).order_by(User.name)
        if not include_deleted:
            statement = statement.where(User.deleted_at.is_(None))
        return list(self._session.execute(statement).scalars().all())

    def update(
        self,
        user_id: UUID,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role: UserRole | None = None,
        commit: bool = True,
    ) -> User | None:
        """Update user information.

        Args:
            user_id: User's primary key
            name: New name (optional)
            email: New email (optional)
            is_active: New active status (optional)
            role: New role (optional)

        Returns:
            Updated User if found, None otherwise

        Raises:
            ValueError: If new email already exists
        """
        user = self.get_by_id(user_id, include_deleted=True)
        if not user:
            return None

        if email is not None and email != user.email:
            existing = self.get_by_email(email, include_deleted=True)
            if existing:
                raise ValueError(f"User with email '{email}' already exists")
            user.email = email

        if name is not None:
            user.name = name
        if is_active is not None:
            user.is_active = is_active
        if role is not None:
            user.role = role

        user.updated_at = datetime.utcnow()
        if commit:
            self._session.commit()
        else:
            self._session.flush()
        self._session.refresh(user)
        return user

    def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user by setting deleted_at timestamp.

        Args:
            user_id: User's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        user = self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is not None:
            return False

        user.deleted_at = datetime.utcnow()
        user.is_active = False
        self._session.commit()
        return True

    def restore(self, user_id: UUID) -> bool:
        """Restore a soft-deleted user.

        Args:
            user_id: User's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        user = self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return False

        user.deleted_at = None
        self._session.commit()
        return True


class SQLClientRepository(ClientRepository):
    """SQL implementation of Client repository with soft delete."""

    def __init__(self, session: Session):
        self._session = session

    def _check_tax_id_exists(self, tax_id: str, exclude_id: int | None = None) -> bool:
        """Check if tax_id already exists.

        Args:
            tax_id: Tax ID to check
            exclude_id: Optional client ID to exclude from check

        Returns:
            True if exists, False otherwise
        """
        statement = select(Client).where(Client.tax_id == tax_id)
        if exclude_id:
            statement = statement.where(Client.id != exclude_id)
        existing = self._session.execute(statement).scalars().first()
        return existing is not None

    def create_individual(
        self,
        tax_id: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        created_by_id: UUID | None = None,
    ) -> Client:
        """Create a new individual client.

        Args:
            tax_id: Tax/RUT identifier
            first_name: First name
            last_name: Last name
            email: Email address (optional)
            phone: Phone number (optional)
            address: Physical address (optional)
            created_by_id: ID of the user who created the client (optional)

        Returns:
            Created Client instance

        Raises:
            ValueError: If tax_id already exists
        """
        if self._check_tax_id_exists(tax_id):
            raise ValueError(f"Client with tax_id '{tax_id}' already exists")

        client = Client(
            client_type=ClientType.INDIVIDUAL,
            tax_id=tax_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            created_by_id=created_by_id,
        )
        self._session.add(client)
        self._session.commit()
        self._session.refresh(client)
        return client

    def create_company(
        self,
        tax_id: str,
        company_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        created_by_id: UUID | None = None,
    ) -> Client:
        """Create a new company client.

        Args:
            tax_id: Tax/RUT identifier
            company_name: Company name
            email: Email address (optional)
            phone: Phone number (optional)
            address: Physical address (optional)
            created_by_id: ID of the user who created the client (optional)

        Returns:
            Created Client instance

        Raises:
            ValueError: If tax_id already exists
        """
        if self._check_tax_id_exists(tax_id):
            raise ValueError(f"Client with tax_id '{tax_id}' already exists")

        client = Client(
            client_type=ClientType.COMPANY,
            tax_id=tax_id,
            company_name=company_name,
            email=email,
            phone=phone,
            address=address,
            created_by_id=created_by_id,
        )
        self._session.add(client)
        self._session.commit()
        self._session.refresh(client)
        return client

    def get_by_id(self, client_id: int, include_deleted: bool = False) -> Client | None:
        """Get client by ID.

        Args:
            client_id: Client's primary key
            include_deleted: If True, include soft-deleted clients

        Returns:
            Client if found, None otherwise
        """
        client = self._session.get(Client, client_id)
        if client and not include_deleted and client.deleted_at is not None:
            return None
        return client

    def get_by_tax_id(self, tax_id: str, include_deleted: bool = False) -> Client | None:
        """Get client by tax ID.

        Args:
            tax_id: Tax/RUT identifier
            include_deleted: If True, include soft-deleted clients

        Returns:
            Client if found, None otherwise
        """
        statement = select(Client).where(Client.tax_id == tax_id)
        client = self._session.execute(statement).scalars().first()
        if client and not include_deleted and client.deleted_at is not None:
            return None
        return client

    def list_all(self, include_deleted: bool = False) -> list[Client]:
        """List all clients.

        Args:
            include_deleted: If True, include soft-deleted clients

        Returns:
            List of clients ordered by name
        """
        statement = select(Client).order_by(Client.first_name).order_by(Client.company_name)
        if not include_deleted:
            statement = statement.where(Client.deleted_at.is_(None))
        return list(self._session.execute(statement).scalars().all())

    def update(
        self,
        client_id: int,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company_name: str | None = None,
    ) -> Client | None:
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
        client = self.get_by_id(client_id, include_deleted=True)
        if not client:
            return None

        if email is not None:
            client.email = email
        if phone is not None:
            client.phone = phone
        if address is not None:
            client.address = address
        if first_name is not None:
            client.first_name = first_name
        if last_name is not None:
            client.last_name = last_name
        if company_name is not None:
            client.company_name = company_name

        client.updated_at = datetime.utcnow()
        self._session.commit()
        self._session.refresh(client)
        return client

    def soft_delete(self, client_id: int) -> bool:
        """Soft delete a client by setting deleted_at timestamp.

        Args:
            client_id: Client's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        client = self.get_by_id(client_id, include_deleted=True)
        if not client or client.deleted_at is not None:
            return False

        client.deleted_at = datetime.utcnow()
        self._session.commit()
        return True

    def restore(self, client_id: int) -> bool:
        """Restore a soft-deleted client.

        Args:
            client_id: Client's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        client = self.get_by_id(client_id, include_deleted=True)
        if not client or client.deleted_at is None:
            return False

        client.deleted_at = None
        self._session.commit()
        return True


class SQLPaperRepository(PaperRepository):
    """SQL implementation of Paper repository with soft delete."""

    def __init__(self, session: Session):
        self._session = session

    def _check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if paper name already exists.

        Args:
            name: Name to check
            exclude_id: Optional paper ID to exclude from check

        Returns:
            True if exists, False otherwise
        """
        statement = select(Paper).where(Paper.name == name)
        if exclude_id:
            statement = statement.where(Paper.id != exclude_id)
        existing = self._session.execute(statement).scalars().first()
        return existing is not None

    def create(
        self,
        name: str,
        weight: int,
        description: str | None = None,
        internal_costs: list[dict] | None = None,
    ) -> Paper:
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
        if self._check_name_exists(name):
            raise ValueError(f"Paper with name '{name}' already exists")

        paper = Paper(
            name=name,
            weight=weight,
            description=description,
            is_active=True,
        )
        try:
            self._session.add(paper)
            self._session.flush()
            self.replace_internal_costs(paper.id, internal_costs or [], commit=False)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._session.refresh(paper)
        return paper

    def list_internal_costs(self, paper_id: int) -> list[PaperInternalCost]:
        return list(
            self._session.execute(
                select(PaperInternalCost).where(PaperInternalCost.paper_id == paper_id)
            ).scalars()
        )

    def replace_internal_costs(
        self, paper_id: int, costs: list[dict], *, commit: bool = True
    ) -> list[PaperInternalCost]:
        print_types = [cost["print_type"] for cost in costs]
        if len(print_types) != len(set(print_types)):
            raise ValueError("duplicate paper internal cost print_type")
        for cost in costs:
            validate_paper_unit(cost["print_type"], cost["unit"])
            if cost.get("paper_cost") is None and cost.get("printing_cost") is None:
                raise ValueError(
                    "paper internal cost row must configure paper_cost or printing_cost"
                )
        for existing in self.list_internal_costs(paper_id):
            self._session.delete(existing)
        self._session.flush()
        for cost in costs:
            self._session.add(PaperInternalCost(paper_id=paper_id, **cost))
        if commit:
            self._session.commit()
        return self.list_internal_costs(paper_id)

    def get_by_id(self, paper_id: int, include_deleted: bool = False) -> Paper | None:
        """Get paper by ID.

        Args:
            paper_id: Paper's primary key
            include_deleted: If True, include soft-deleted papers

        Returns:
            Paper if found, None otherwise
        """
        paper = self._session.get(Paper, paper_id)
        if paper and not include_deleted and paper.deleted_at is not None:
            return None
        return paper

    def get_by_name(self, name: str, include_deleted: bool = False) -> Paper | None:
        """Get paper by name.

        Args:
            name: Paper name
            include_deleted: If True, include soft-deleted papers

        Returns:
            Paper if found, None otherwise
        """
        statement = select(Paper).where(Paper.name == name)
        paper = self._session.execute(statement).scalars().first()
        if paper and not include_deleted and paper.deleted_at is not None:
            return None
        return paper

    def list_all(self, include_deleted: bool = False) -> list[Paper]:
        """List all papers.

        Args:
            include_deleted: If True, include soft-deleted papers

        Returns:
            List of papers ordered by name
        """
        statement = select(Paper).order_by(Paper.name)
        if not include_deleted:
            statement = statement.where(Paper.deleted_at.is_(None))
        return list(self._session.execute(statement).scalars().all())

    def get_plotter_papers(self) -> list[Paper]:
        """Return active papers that have at least one Plotter catalog rate."""
        statement = (
            select(Paper)
            .join(PlotterPricing, PlotterPricing.paper_id == Paper.id)
            .where(Paper.deleted_at.is_(None))
            .where(Paper.is_active.is_(True))
            .distinct()
            .order_by(Paper.name)
        )
        return list(self._session.execute(statement).scalars().all())

    def get_papers_by_color_mode(self, print_type: PrintType, color_mode: ColorMode) -> list[Paper]:
        """Get papers that have pricing for specific print type and color mode.

        Args:
            print_type: Type of printing (DIGITAL, OFFSET, PLOTTER)
            color_mode: Color mode (C4_0, C4_4)

        Returns:
            List of papers with pricing for the given print_type and color_mode
        """
        # Find papers that have pricing entries matching the criteria
        statement = (
            select(Paper)
            .join(PaperPricing)
            .where(Paper.deleted_at.is_(None))
            .where(Paper.is_active.is_(True))
            .where(PaperPricing.print_type == print_type)
            .where((PaperPricing.color_mode == color_mode) | (PaperPricing.color_mode.is_(None)))
            .distinct()
            .order_by(Paper.name)
        )
        return list(self._session.execute(statement).scalars().all())

    def list_active(self) -> list[Paper]:
        """List only active (non-deleted and is_active=True) papers.

        Returns:
            List of active papers ordered by name
        """
        statement = (
            select(Paper)
            .where(Paper.deleted_at.is_(None))
            .where(Paper.is_active.is_(True))
            .order_by(Paper.name)
        )
        return list(self._session.execute(statement).scalars().all())

    def update(
        self,
        paper_id: int,
        name: str | None = None,
        weight: int | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        internal_costs: list[dict] | None = None,
    ) -> Paper | None:
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
        paper = self.get_by_id(paper_id, include_deleted=True)
        if not paper:
            return None

        if name is not None and name != paper.name:
            if self._check_name_exists(name, exclude_id=paper_id):
                raise ValueError(f"Paper with name '{name}' already exists")
            paper.name = name

        if weight is not None:
            paper.weight = weight
        if description is not None:
            paper.description = description
        if is_active is not None:
            paper.is_active = is_active

        if internal_costs is not None:
            self.replace_internal_costs(paper_id, internal_costs, commit=False)

        paper.updated_at = datetime.utcnow()
        self._session.commit()
        # The relationship may still contain deleted cost rows after replacement.
        self._session.expire(paper, ["internal_costs"])
        self._session.refresh(paper)
        return paper

    def soft_delete(self, paper_id: int) -> bool:
        """Soft delete a paper by setting deleted_at timestamp.

        Args:
            paper_id: Paper's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        paper = self.get_by_id(paper_id, include_deleted=True)
        if not paper or paper.deleted_at is not None:
            return False

        paper.deleted_at = datetime.utcnow()
        paper.is_active = False
        self._session.commit()
        return True

    def restore(self, paper_id: int) -> bool:
        """Restore a soft-deleted paper.

        Args:
            paper_id: Paper's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        paper = self.get_by_id(paper_id, include_deleted=True)
        if not paper or paper.deleted_at is None:
            return False

        paper.deleted_at = None
        self._session.commit()
        return True

    def _check_overlap(
        self,
        paper_id: int,
        print_type,
        min_quantity: int,
        max_quantity: int | None,
        exclude_id: int | None = None,
    ):
        """Check if a quantity range overlaps with existing pricing entries.

        Overlap exists if:
        (new_min <= existing_max OR existing_max is NULL)
        AND
        (existing_min <= new_max OR new_max is NULL)
        """
        from quote.repo.models import PaperPricing

        statement = (
            select(PaperPricing)
            .where(PaperPricing.paper_id == paper_id)
            .where(PaperPricing.print_type == print_type)
        )

        if exclude_id:
            statement = statement.where(PaperPricing.id != exclude_id)

        # Condition: existing_min <= new_max (if new_max is not None)
        if max_quantity is not None:
            statement = statement.where(PaperPricing.min_quantity <= max_quantity)

        # Condition: new_min <= existing_max (if existing_max is not None)
        # If existing_max is None, it's infinity, so new_min will always be <= existing_max
        statement = statement.where(
            or_(
                PaperPricing.max_quantity == None,
                PaperPricing.max_quantity >= min_quantity,
            )
        )

        existing = self._session.execute(statement).scalars().first()
        if existing:
            raise ValueError(
                f"Overlapping pricing range found: {existing.min_quantity}-"
                f"{existing.max_quantity or '∞'} overlaps with "
                f"{min_quantity}-{max_quantity or '∞'}"
            )

    def list_pricing(self, paper_id: int) -> list[PaperPricing]:
        """List all pricing entries for a paper.

        Args:
            paper_id: Paper's primary key

        Returns:
            List of PaperPricing entries ordered by print_type and min_quantity
        """
        from quote.repo.models import PaperPricing

        statement = (
            select(PaperPricing)
            .where(PaperPricing.paper_id == paper_id)
            .order_by(PaperPricing.print_type, PaperPricing.min_quantity)
        )
        return list(self._session.execute(statement).scalars().all())

    def create_pricing(
        self,
        paper_id: int,
        print_type,
        min_quantity: int,
        max_quantity: int | None,
        unit_price: Decimal,
    ) -> PaperPricing:
        """Create a new pricing entry for a paper.

        Args:
            paper_id: Paper's primary key
            print_type: Type of printing (DIGITAL, OFFSET, PLOTTER)
            min_quantity: Minimum quantity for this price range
            max_quantity: Maximum quantity (None = unlimited)
            unit_price: Price per unit

        Returns:
            Created PaperPricing instance
        """
        from quote.repo.models import PaperPricing

        # Check for overlaps
        self._check_overlap(paper_id, print_type, min_quantity, max_quantity)

        pricing = PaperPricing(
            paper_id=paper_id,
            print_type=print_type,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            unit_price=unit_price,
        )
        self._session.add(pricing)
        self._session.commit()
        self._session.refresh(pricing)
        return pricing

    def get_pricing_by_id(self, pricing_id: int) -> PaperPricing | None:
        """Get a pricing entry by ID.

        Args:
            pricing_id: Pricing entry's primary key

        Returns:
            PaperPricing if found, None otherwise
        """
        from quote.repo.models import PaperPricing

        return self._session.get(PaperPricing, pricing_id)

    def update_pricing(
        self,
        pricing_id: int,
        print_type=None,
        min_quantity: int | None = None,
        max_quantity: int | None = None,
        unit_price: Decimal | None = None,
    ) -> PaperPricing | None:
        """Update a pricing entry.

        Args:
            pricing_id: Pricing entry's primary key
            print_type: New print type (optional)
            min_quantity: New minimum quantity (optional)
            max_quantity: New maximum quantity (optional)
            unit_price: New unit price (optional)

        Returns:
            Updated PaperPricing if found, None otherwise
        """
        pricing = self.get_pricing_by_id(pricing_id)
        if not pricing:
            return None

        # Check for overlaps if range or type changes
        if any(x is not None for x in [print_type, min_quantity, max_quantity]):
            new_print_type = print_type if print_type is not None else pricing.print_type
            new_min = min_quantity if min_quantity is not None else pricing.min_quantity
            # Special case for max_quantity because None is a valid value (infinity)
            # But the parameter max_quantity=None means "not provided for update"
            # unless we distinguish between "not provided" and "set to None".
            # In current implementation, max_quantity=None in kwargs means it wasn't passed.
            # Wait, schemas use optional fields.
            new_max = max_quantity if max_quantity is not None else pricing.max_quantity

            self._check_overlap(
                pricing.paper_id, new_print_type, new_min, new_max, exclude_id=pricing_id
            )

        if print_type is not None:
            pricing.print_type = print_type
        if min_quantity is not None:
            pricing.min_quantity = min_quantity
        if max_quantity is not None:
            pricing.max_quantity = max_quantity
        if unit_price is not None:
            pricing.unit_price = unit_price

        self._session.commit()
        self._session.refresh(pricing)
        return pricing

    def delete_pricing(self, pricing_id: int) -> bool:
        """Delete a pricing entry.

        Args:
            pricing_id: Pricing entry's primary key

        Returns:
            True if deleted, False if not found
        """
        pricing = self.get_pricing_by_id(pricing_id)
        if not pricing:
            return False

        self._session.delete(pricing)
        self._session.commit()
        return True


class SQLFinishRepository(FinishRepository):
    """SQL implementation of Finish repository with soft delete."""

    def __init__(self, session: Session):
        self._session = session

    def _check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if finish name already exists.

        Args:
            name: Name to check
            exclude_id: Optional finish ID to exclude from check

        Returns:
            True if exists, False otherwise
        """
        statement = select(Finish).where(Finish.name == name)
        if exclude_id:
            statement = statement.where(Finish.id != exclude_id)
        existing = self._session.execute(statement).scalars().first()
        return existing is not None

    def create(
        self,
        name: str,
        description: str | None = None,
        internal_costs: list[dict] | None = None,
    ) -> Finish:
        """Create a new finish.

        Args:
            name: Finish name (e.g., "Corte Recto")
            description: Optional description

        Returns:
            Created Finish instance

        Raises:
            ValueError: If name already exists
        """
        if self._check_name_exists(name):
            raise ValueError(f"Finish with name '{name}' already exists")

        finish = Finish(
            name=name,
            description=description,
            is_active=True,
        )
        try:
            self._session.add(finish)
            self._session.flush()
            self.replace_internal_costs(finish.id, internal_costs or [], commit=False)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._session.refresh(finish)
        return finish

    def list_internal_costs(self, finish_id: int) -> list[FinishInternalCost]:
        return list(
            self._session.execute(
                select(FinishInternalCost).where(FinishInternalCost.finish_id == finish_id)
            ).scalars()
        )

    def replace_internal_costs(
        self, finish_id: int, costs: list[dict], *, commit: bool = True
    ) -> list[FinishInternalCost]:
        print_types = [cost["print_type"] for cost in costs]
        if len(print_types) != len(set(print_types)):
            raise ValueError("duplicate finish internal cost print_type")
        for cost in costs:
            validate_finish_unit(cost["print_type"], cost["unit"])
            if Decimal(str(cost["unit_cost"])) < 0:
                raise ValueError("internal cost must be non-negative")
        for existing in self.list_internal_costs(finish_id):
            self._session.delete(existing)
        self._session.flush()
        for cost in costs:
            self._session.add(FinishInternalCost(finish_id=finish_id, **cost))
        if commit:
            self._session.commit()
        return self.list_internal_costs(finish_id)

    def get_by_id(self, finish_id: int, include_deleted: bool = False) -> Finish | None:
        """Get finish by ID.

        Args:
            finish_id: Finish's primary key
            include_deleted: If True, include soft-deleted finishes

        Returns:
            Finish if found, None otherwise
        """
        finish = self._session.get(Finish, finish_id)
        if finish and not include_deleted and finish.deleted_at is not None:
            return None
        return finish

    def get_by_name(self, name: str, include_deleted: bool = False) -> Finish | None:
        """Get finish by name.

        Args:
            name: Finish name
            include_deleted: If True, include soft-deleted finishes

        Returns:
            Finish if found, None otherwise
        """
        statement = select(Finish).where(Finish.name == name)
        finish = self._session.execute(statement).scalars().first()
        if finish and not include_deleted and finish.deleted_at is not None:
            return None
        return finish

    def list_all(self, include_deleted: bool = False) -> list[Finish]:
        """List all finishes.

        Args:
            include_deleted: If True, include soft-deleted finishes

        Returns:
            List of finishes ordered by name
        """
        statement = select(Finish).order_by(Finish.name)
        if not include_deleted:
            statement = statement.where(Finish.deleted_at.is_(None))
        return list(self._session.execute(statement).scalars().all())

    def list_active(self) -> list[Finish]:
        """List only active (non-deleted and is_active=True) finishes.

        Returns:
            List of active finishes ordered by name
        """
        statement = (
            select(Finish)
            .where(Finish.deleted_at.is_(None))
            .where(Finish.is_active.is_(True))
            .order_by(Finish.name)
        )
        return list(self._session.execute(statement).scalars().all())

    def get_plotter_finishes(self) -> list[Finish]:
        """Return active finishes that have at least one Plotter catalog rate."""
        statement = (
            select(Finish)
            .join(PlotterPricing, PlotterPricing.finish_id == Finish.id)
            .where(Finish.deleted_at.is_(None))
            .where(Finish.is_active.is_(True))
            .distinct()
            .order_by(Finish.name)
        )
        return list(self._session.execute(statement).scalars().all())

    def update(
        self,
        finish_id: int,
        name: str | None = None,
        finish_type: FinishType | None = None,
        unit: Unit | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        internal_costs: list[dict] | None = None,
    ) -> Finish | None:
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
        finish = self.get_by_id(finish_id, include_deleted=True)
        if not finish:
            return None

        if name is not None and name != finish.name:
            if self._check_name_exists(name, exclude_id=finish_id):
                raise ValueError(f"Finish with name '{name}' already exists")
            finish.name = name

        if finish_type is not None:
            finish.finish_type = finish_type
        if unit is not None:
            finish.unit = unit
        if description is not None:
            finish.description = description
        if is_active is not None:
            finish.is_active = is_active

        if internal_costs is not None:
            self.replace_internal_costs(finish_id, internal_costs, commit=False)

        finish.updated_at = datetime.utcnow()
        self._session.commit()
        # Reload the replaced relationship before response-model serialization.
        self._session.expire(finish, ["internal_costs"])
        self._session.refresh(finish)
        return finish

    def soft_delete(self, finish_id: int) -> bool:
        """Soft delete a finish by setting deleted_at timestamp.

        Args:
            finish_id: Finish's primary key

        Returns:
            True if deleted, False if not found or already deleted
        """
        finish = self.get_by_id(finish_id, include_deleted=True)
        if not finish or finish.deleted_at is not None:
            return False

        finish.deleted_at = datetime.utcnow()
        finish.is_active = False
        self._session.commit()
        return True

    def restore(self, finish_id: int) -> bool:
        """Restore a soft-deleted finish.

        Args:
            finish_id: Finish's primary key

        Returns:
            True if restored, False if not found or not deleted
        """
        finish = self.get_by_id(finish_id, include_deleted=True)
        if not finish or finish.deleted_at is None:
            return False

        finish.deleted_at = None
        self._session.commit()
        return True

    def _check_overlap(
        self,
        finish_id: int,
        print_type,
        min_quantity: int,
        max_quantity: int | None,
        exclude_id: int | None = None,
    ):
        """Check if a quantity range overlaps with existing pricing entries.

        Overlap exists if:
        (new_min <= existing_max OR existing_max is NULL)
        AND
        (existing_min <= new_max OR new_max is NULL)
        """
        from quote.repo.models import FinishPricing

        statement = (
            select(FinishPricing)
            .where(FinishPricing.finish_id == finish_id)
            .where(FinishPricing.print_type == print_type)
        )

        if exclude_id:
            statement = statement.where(FinishPricing.id != exclude_id)

        # Condition: existing_min <= new_max (if new_max is not None)
        if max_quantity is not None:
            statement = statement.where(FinishPricing.min_quantity <= max_quantity)

        # Condition: new_min <= existing_max (if existing_max is not None)
        statement = statement.where(
            or_(
                FinishPricing.max_quantity == None,
                FinishPricing.max_quantity >= min_quantity,
            )
        )

        existing = self._session.execute(statement).scalars().first()
        if existing:
            raise ValueError(
                f"Overlapping pricing range found: {existing.min_quantity}-"
                f"{existing.max_quantity or '∞'} overlaps with "
                f"{min_quantity}-{max_quantity or '∞'}"
            )

    def list_pricing(self, finish_id: int) -> list[FinishPricing]:
        """List all pricing entries for a finish.

        Args:
            finish_id: Finish's primary key

        Returns:
            List of FinishPricing entries ordered by print_type and min_quantity
        """
        from quote.repo.models import FinishPricing

        statement = (
            select(FinishPricing)
            .where(FinishPricing.finish_id == finish_id)
            .order_by(FinishPricing.print_type, FinishPricing.min_quantity)
        )
        return list(self._session.execute(statement).scalars().all())

    def create_pricing(
        self,
        finish_id: int,
        print_type,
        unit,
        min_quantity: int,
        max_quantity: int | None,
        unit_price: Decimal,
    ) -> FinishPricing:
        """Create a new pricing entry for a finish.

        Args:
            finish_id: Finish's primary key
            print_type: Type of printing (DIGITAL, OFFSET, PLOTTER)
            unit: Unit of measurement (JOB, PER_ITEM, etc.)
            min_quantity: Minimum quantity for this price range
            max_quantity: Maximum quantity (None = unlimited)
            unit_price: Price per unit

        Returns:
            Created FinishPricing instance
        """
        from quote.repo.models import FinishPricing

        # Check for overlaps
        self._check_overlap(finish_id, print_type, min_quantity, max_quantity)

        pricing = FinishPricing(
            finish_id=finish_id,
            print_type=print_type,
            unit=unit,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            unit_price=unit_price,
        )
        self._session.add(pricing)
        self._session.commit()
        self._session.refresh(pricing)
        return pricing

    def get_pricing_by_id(self, pricing_id: int) -> FinishPricing | None:
        """Get a pricing entry by ID.

        Args:
            pricing_id: Pricing entry's primary key

        Returns:
            FinishPricing if found, None otherwise
        """
        from quote.repo.models import FinishPricing

        return self._session.get(FinishPricing, pricing_id)

    def update_pricing(
        self,
        pricing_id: int,
        print_type=None,
        unit=None,
        min_quantity: int | None = None,
        max_quantity: int | None = None,
        unit_price: Decimal | None = None,
    ) -> FinishPricing | None:
        """Update a pricing entry.

        Args:
            pricing_id: Pricing entry's primary key
            print_type: New print type (optional)
            unit: New unit (optional)
            min_quantity: New minimum quantity (optional)
            max_quantity: New maximum quantity (optional)
            unit_price: New unit price (optional)

        Returns:
            Updated FinishPricing if found, None otherwise
        """
        pricing = self.get_pricing_by_id(pricing_id)
        if not pricing:
            return None

        # Check for overlaps if range or type changes
        if any(x is not None for x in [print_type, min_quantity, max_quantity]):
            new_print_type = print_type if print_type is not None else pricing.print_type
            new_min = min_quantity if min_quantity is not None else pricing.min_quantity
            new_max = max_quantity if max_quantity is not None else pricing.max_quantity

            self._check_overlap(
                pricing.finish_id, new_print_type, new_min, new_max, exclude_id=pricing_id
            )

        if print_type is not None:
            pricing.print_type = print_type
        if unit is not None:
            pricing.unit = unit
        if min_quantity is not None:
            pricing.min_quantity = min_quantity
        if max_quantity is not None:
            pricing.max_quantity = max_quantity
        if unit_price is not None:
            pricing.unit_price = unit_price

        self._session.commit()
        self._session.refresh(pricing)
        return pricing

    def delete_pricing(self, pricing_id: int) -> bool:
        """Delete a pricing entry.

        Args:
            pricing_id: Pricing entry's primary key

        Returns:
            True if deleted, False if not found
        """
        pricing = self.get_pricing_by_id(pricing_id)
        if not pricing:
            return False

        self._session.delete(pricing)
        self._session.commit()
        return True
