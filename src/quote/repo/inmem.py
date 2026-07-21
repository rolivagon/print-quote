"""In-memory repository implementations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from quote.domain.enums import ClientType, FinishType, PrintType, Unit, UserRole
from quote.domain.models import FixedProduct as FixedProductDomain
from quote.domain.models import QuantityRange, QuoteBreakdown
from quote.repo.models import Client, Finish, FixedProductQuantityRange, Paper, Quote, User

from .interfaces import (
    ClientRepository,
    DigitalPriceRepository,
    FinancialRulesRepository,
    FinishRepository,
    FixedProductRepository,
    GeometryRepository,
    OffsetPriceRepository,
    PaperRepository,
    PlotterPriceRepository,
    QuoteRepository,
    UserRepository,
)


class InMemoryQuoteRepository(QuoteRepository):
    """In-memory implementation of quote repository."""

    def __init__(self):
        self._quotes: dict[str, Quote] = {}

    def save(self, quote: Quote) -> Quote:
        """Save a quote to memory."""
        self._quotes[quote.quote_number] = quote
        return quote

    def get_by_id(self, quote_id: str) -> Quote | None:
        """Get a quote by ID from memory."""
        return self._quotes.get(quote_id)


class InMemoryDigitalPriceRepository(DigitalPriceRepository):
    """In-memory implementation of digital price repository with test values."""

    def get_price_table_by_color_config(self, color_config: str) -> list[tuple[int, int, Decimal]]:
        """Get price table by color configuration."""
        tables = {
            "4/0": [
                (1, 10, Decimal("1000")),  # placeholder
                (11, 50, Decimal("900")),  # placeholder
                (51, 100, Decimal("715")),  # valor real para 500 flyers
                (101, float("inf"), Decimal("650")),  # placeholder
            ],
            "4/4": [
                (1, 10, Decimal("2500")),  # placeholder
                (11, 50, Decimal("2200")),  # placeholder
                (51, 100, Decimal("2090")),  # valor real para 300 tarjetas
                (101, float("inf"), Decimal("1900")),  # placeholder
            ],
            "diploma_4/0": [
                (
                    1,
                    float("inf"),
                    Decimal("1760"),
                )  # Precio fijo para diplomas, todas las cantidades
            ],
        }
        return tables.get(color_config, [])

    def get_finishing_prices(self) -> dict[str, dict[str, any]]:
        """Get finishing prices with mode and price."""
        return {"corte_recto": {"mode": "per_job", "price": Decimal("3000")}}


class InMemoryPlotterPriceRepository(PlotterPriceRepository):
    """In-memory implementation of plotter price repository with test values."""

    def get_material_prices(self) -> dict[str, Decimal]:
        """Get material prices per square meter."""
        return {
            "sintetico": Decimal("8500"),  # por m²
            "lona_pvc": Decimal("8500"),  # por m²
        }

    def get_finishing_prices(self) -> dict[str, dict[str, any]]:
        """Get finishing prices with mode and price."""
        return {
            "corte_recto": {"mode": "per_job", "price": Decimal("1000")},
            "ojetillos": {"mode": "per_quantity", "price": Decimal("500")},
        }

    def get_minimum_charge_sqm(self) -> Decimal:
        """Get minimum chargeable square meters."""
        return Decimal("0.25")


class InMemoryOffsetPriceRepository(OffsetPriceRepository):
    """In-memory implementation of offset price repository with test values."""

    def get_plates_price_per_color(self) -> Decimal:
        """Get price per color for plates."""
        return Decimal("7000")  # $7.000 por color

    def get_run_price_table(self) -> dict[int, Decimal]:
        """Get run prices by quantity."""
        return {
            1000: Decimal("50000"),  # placeholder
            2000: Decimal("80000"),  # placeholder
            5000: Decimal("170000"),  # valor real
        }

    def get_finishing_price_table(self, finishing_type: str) -> dict[int, Decimal]:
        """Get finishing prices by quantity for specific finishing type."""
        if finishing_type == "troquel":
            return {
                1000: Decimal("70000"),  # placeholder
                5000: Decimal("60000"),  # valor real
            }
        return {}

    def get_fixed_costs(self) -> dict[str, Decimal]:
        """Get fixed costs like molds, setup fees, etc."""
        return {"molde_troquel": Decimal("20000")}

    def get_merma_per_design(self) -> int:
        """Get merma (waste) sheets per design."""
        return 300


class InMemoryGeometryRepository(GeometryRepository):
    """In-memory implementation of geometry repository with test values."""

    def get_default_geometry(self) -> dict[str, any]:
        """Get default geometry parameters."""
        return {"bleed_mm": 3, "margin_mm": 5, "gap_mm": 3, "allow_rotate": True}

    def get_standard_sheet_sizes(self) -> dict[str, dict[str, float]]:
        """Get standard sheet sizes for each print type."""
        return {
            "digital_sheet": {
                "width_cm": 30,
                "height_cm": 45,
                "usable_width_cm": 29,
                "usable_height_cm": 44,
            },
            "offset_sheet": {"width_cm": 66, "height_cm": 44},
            "plotter_minimum_m2": 0.25,
        }


class InMemoryFinancialRulesRepository(FinancialRulesRepository):
    """In-memory implementation of financial rules repository with test values."""

    def get_vat_rate(self) -> Decimal:
        """Get VAT/IVA rate."""
        return Decimal("0.19")  # 19%

    def get_markup_rates(self) -> dict[str, Decimal]:
        """Get markup rates by print category."""
        return {"DIGITAL": Decimal("0"), "PLOTTER": Decimal("0"), "OFFSET": Decimal("0")}

    def get_rounding_mode(self) -> str:
        """Get rounding mode (hundreds, tens, units)."""
        return "hundreds"  # redondear al múltiplo de $100


class InMemoryFixedProductRepository(FixedProductRepository):
    """In-memory implementation of fixed product repository."""

    def __init__(self):
        self._products: dict[str, FixedProductDomain] = {}
        self._ranges: dict[
            str, dict[str, QuantityRange]
        ] = {}  # product_id -> {range_id: QuantityRange}
        self._range_id_counter = 0

    def create(
        self,
        product_id: str,
        name: str,
        print_type: str,
        base_quote_snapshot: dict,
        client_id: int | None = None,
    ) -> FixedProductDomain:
        """Create a new fixed product without ranges."""

        # Create a minimal QuoteBreakdown for the base_quote
        total_final = Decimal(base_quote_snapshot.get("calculated_total", "0"))
        base_quote = QuoteBreakdown(
            print_type=PrintType(print_type.lower()),
            quantity=base_quote_snapshot.get("quantity", 0),
            pieces_per_sheet=base_quote_snapshot.get("pieces_per_sheet"),
            sheets_needed=base_quote_snapshot.get("sheets_needed"),
            total_sheets_with_merma=base_quote_snapshot.get("total_sheets_with_merma"),
            material_cost=Decimal("0"),
            finishing_cost=Decimal("0"),
            subtotal_before_markup=Decimal("0"),
            markup_applied=Decimal("0"),
            subtotal_with_markup=Decimal("0"),
            net_before_iva=total_final if total_final > 0 else Decimal("1"),
            iva_amount=Decimal("0"),
            total_final=total_final if total_final > 0 else Decimal("1"),
        )

        product = FixedProductDomain(
            id=product_id,
            name=name,
            base_quote=base_quote,
            quantity_ranges=[],
            print_type=PrintType(print_type.lower()),
            client_id=str(client_id) if client_id else None,
        )
        self._products[product_id] = product
        self._ranges[product_id] = {}
        return product

    def get_by_uuid(self, uuid: str) -> FixedProductDomain | None:
        """Get a fixed product by UUID."""
        product = self._products.get(uuid)
        if product:
            # Refresh ranges from storage
            product.quantity_ranges = list(self._ranges.get(uuid, {}).values())
        return product

    def get_by_product_id(self, product_id: str) -> FixedProductDomain | None:
        """Get a fixed product by product_id (slug)."""
        product = self._products.get(product_id)
        if product:
            # Refresh ranges from storage
            product.quantity_ranges = list(self._ranges.get(product_id, {}).values())
        return product

    def list_all(
        self, client_id: int | None = None, include_globals: bool = True
    ) -> list[FixedProductDomain]:
        """List all fixed products."""
        results = []
        for product_id, product in self._products.items():
            # Refresh ranges
            product.quantity_ranges = list(self._ranges.get(product_id, {}).values())

            if client_id is None:
                if include_globals or product.client_id is None:
                    results.append(product)
            else:
                if product.client_id == str(client_id):
                    results.append(product)
                elif include_globals and product.client_id is None:
                    results.append(product)
        return results

    def add_range(
        self,
        product_uuid: str,
        min_quantity: int,
        max_quantity: int,
        unit_price: Decimal,
    ) -> "FixedProductQuantityRange":
        """Add a quantity range to a fixed product."""
        if product_uuid not in self._products:
            raise ValueError(f"Product {product_uuid} not found")

        # Check for overlaps
        if self.check_range_overlap(product_uuid, min_quantity, max_quantity):
            raise ValueError(f"Range {min_quantity}-{max_quantity} overlaps with existing ranges")

        self._range_id_counter += 1
        range_id = f"range_{self._range_id_counter}"

        range_obj = QuantityRange(
            min_qty=min_quantity,
            max_qty=max_quantity,
            unit_price=unit_price,
        )

        if product_uuid not in self._ranges:
            self._ranges[product_uuid] = {}

        self._ranges[product_uuid][range_id] = range_obj

        # Update product's ranges
        self._products[product_uuid].quantity_ranges = list(self._ranges[product_uuid].values())

        return range_obj

    def update_range(
        self,
        range_id: str,
        min_quantity: int | None = None,
        max_quantity: int | None = None,
        unit_price: Decimal | None = None,
    ) -> "FixedProductQuantityRange | None":
        """Update a quantity range."""
        # Find the range
        for product_id, ranges in self._ranges.items():
            if range_id in ranges:
                existing = ranges[range_id]
                new_min = min_quantity if min_quantity is not None else existing.min_qty
                new_max = max_quantity if max_quantity is not None else existing.max_qty
                new_price = unit_price if unit_price is not None else existing.unit_price

                # Check for overlaps (excluding this range)
                if self.check_range_overlap(
                    product_id, new_min, new_max, exclude_range_id=range_id
                ):
                    raise ValueError(f"Range {new_min}-{new_max} overlaps with existing ranges")

                updated = QuantityRange(
                    min_qty=new_min,
                    max_qty=new_max,
                    unit_price=new_price,
                )
                ranges[range_id] = updated

                # Update product's ranges
                self._products[product_id].quantity_ranges = list(ranges.values())

                return updated

        return None

    def delete_range(self, range_id: str) -> bool:
        """Delete a quantity range."""
        for product_id, ranges in self._ranges.items():
            if range_id in ranges:
                del ranges[range_id]
                # Update product's ranges
                self._products[product_id].quantity_ranges = list(ranges.values())
                return True
        return False

    def delete(self, product_uuid: str) -> bool:
        """Delete a fixed product and all its ranges."""
        if product_uuid in self._products:
            del self._products[product_uuid]
            if product_uuid in self._ranges:
                del self._ranges[product_uuid]
            return True
        return False

    def check_range_overlap(
        self, product_uuid: str, min_qty: int, max_qty: int, exclude_range_id: str | None = None
    ) -> bool:
        """Check if a range overlaps with existing ranges."""
        ranges = self._ranges.get(product_uuid, {})

        for rid, existing in ranges.items():
            if exclude_range_id and rid == exclude_range_id:
                continue
            # Check overlap: A overlaps B if A starts before B ends AND B starts before A ends
            if min_qty <= existing.max_qty and existing.min_qty <= max_qty:
                return True

        return False

    def to_domain(self, product: "FixedProductDomain") -> FixedProductDomain:
        """Convert SQL model to domain model."""
        return product  # Already domain model in memory

    def save(self, product: FixedProductDomain) -> None:
        """Save a fixed product to memory (legacy method)."""
        self._products[product.id] = product

    def get_by_id(self, product_id: str) -> FixedProductDomain | None:
        """Get a fixed product by ID from memory (legacy method)."""
        return self._products.get(product_id)

    def find_by_client(
        self, client_id: str | None = None, include_globals: bool = True
    ) -> list[FixedProductDomain]:
        """Find fixed products by client (legacy method)."""
        results = []
        for product in self._products.values():
            if product.client_id == client_id:
                results.append(product)
            elif include_globals and product.client_id is None:
                results.append(product)
        return results


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of User repository with soft delete."""

    def __init__(self):
        self._users: dict[UUID, User] = {}

    def create(self, name: str, email: str) -> User:
        """Create a new user."""
        for user in self._users.values():
            if user.email == email:
                raise ValueError(f"User with email '{email}' already exists")

        user = User(
            id=uuid4(),
            name=name,
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert user.id is not None
        self._users[user.id] = user
        return user

    def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        """Get user by ID."""
        user = self._users.get(user_id)
        if user and not include_deleted and user.deleted_at is not None:
            return None
        return user

    def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """Get user by email address."""
        for user in self._users.values():
            if user.email == email:
                if not include_deleted and user.deleted_at is not None:
                    return None
                return user
        return None

    def list_all(self, include_deleted: bool = False) -> list[User]:
        """List all users."""
        users = [u for u in self._users.values() if include_deleted or u.deleted_at is None]
        return sorted(users, key=lambda u: u.name)

    def update(
        self,
        user_id: UUID,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role: UserRole | None = None,
        commit: bool = True,
    ) -> User | None:
        """Update user information."""
        user = self.get_by_id(user_id, include_deleted=True)
        if not user:
            return None

        if email is not None and email != user.email:
            for u in self._users.values():
                if u.email == email and u.id != user_id:
                    raise ValueError(f"User with email '{email}' already exists")
            user.email = email

        if name is not None:
            user.name = name
        if is_active is not None:
            user.is_active = is_active
        if role is not None:
            user.role = role

        user.updated_at = datetime.utcnow()
        return user

    def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user."""
        user = self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is not None:
            return False

        user.deleted_at = datetime.utcnow()
        user.is_active = False
        return True

    def restore(self, user_id: UUID) -> bool:
        """Restore a soft-deleted user."""
        user = self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return False

        user.deleted_at = None
        return True


class InMemoryClientRepository(ClientRepository):
    """In-memory implementation of Client repository with soft delete."""

    _next_id: int = 1

    def __init__(self):
        self._clients: dict[int, Client] = {}

    def _check_tax_id_exists(self, tax_id: str, exclude_id: int | None = None) -> bool:
        """Check if tax_id already exists."""
        for client in self._clients.values():
            if client.tax_id == tax_id and client.id != exclude_id:
                return True
        return False

    def create_individual(
        self,
        tax_id: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> Client:
        """Create a new individual client."""
        if self._check_tax_id_exists(tax_id):
            raise ValueError(f"Client with tax_id '{tax_id}' already exists")

        client = Client(
            id=InMemoryClientRepository._next_id,
            client_type=ClientType.INDIVIDUAL,
            tax_id=tax_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            created_at=datetime.utcnow(),
        )
        assert client.id is not None
        self._clients[client.id] = client
        InMemoryClientRepository._next_id += 1
        return client

    def create_company(
        self,
        tax_id: str,
        company_name: str,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> Client:
        """Create a new company client."""
        if self._check_tax_id_exists(tax_id):
            raise ValueError(f"Client with tax_id '{tax_id}' already exists")

        client = Client(
            id=InMemoryClientRepository._next_id,
            client_type=ClientType.COMPANY,
            tax_id=tax_id,
            company_name=company_name,
            email=email,
            phone=phone,
            address=address,
            created_at=datetime.utcnow(),
        )
        assert client.id is not None
        self._clients[client.id] = client
        InMemoryClientRepository._next_id += 1
        return client

    def get_by_id(self, client_id: int, include_deleted: bool = False) -> Client | None:
        """Get client by ID."""
        client = self._clients.get(client_id)
        if client and not include_deleted and client.deleted_at is not None:
            return None
        return client

    def get_by_tax_id(self, tax_id: str, include_deleted: bool = False) -> Client | None:
        """Get client by tax ID."""
        for client in self._clients.values():
            if client.tax_id == tax_id:
                if not include_deleted and client.deleted_at is not None:
                    return None
                return client
        return None

    def list_all(self, include_deleted: bool = False) -> list[Client]:
        """List all clients."""
        clients = [c for c in self._clients.values() if include_deleted or c.deleted_at is None]
        return sorted(
            clients,
            key=lambda c: c.first_name or c.company_name or "",
        )

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
        """Update client information."""
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
        return client

    def soft_delete(self, client_id: int) -> bool:
        """Soft delete a client."""
        client = self.get_by_id(client_id, include_deleted=True)
        if not client or client.deleted_at is not None:
            return False

        client.deleted_at = datetime.utcnow()
        return True

    def restore(self, client_id: int) -> bool:
        """Restore a soft-deleted client."""
        client = self.get_by_id(client_id, include_deleted=True)
        if not client or client.deleted_at is None:
            return False

        client.deleted_at = None
        return True


class InMemoryPaperRepository(PaperRepository):
    """In-memory implementation of Paper repository with soft delete."""

    _next_id: int = 1

    def __init__(self):
        self._papers: dict[int, Paper] = {}

    def _check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if paper name already exists."""
        for paper in self._papers.values():
            if paper.name == name and paper.id != exclude_id:
                return True
        return False

    def create(
        self,
        name: str,
        weight: int,
        description: str | None = None,
    ) -> Paper:
        """Create a new paper."""
        if self._check_name_exists(name):
            raise ValueError(f"Paper with name '{name}' already exists")

        paper = Paper(
            id=InMemoryPaperRepository._next_id,
            name=name,
            weight=weight,
            description=description,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert paper.id is not None
        self._papers[paper.id] = paper
        InMemoryPaperRepository._next_id += 1
        return paper

    def get_by_id(self, paper_id: int, include_deleted: bool = False) -> Paper | None:
        """Get paper by ID."""
        paper = self._papers.get(paper_id)
        if paper and not include_deleted and paper.deleted_at is not None:
            return None
        return paper

    def get_by_name(self, name: str, include_deleted: bool = False) -> Paper | None:
        """Get paper by name."""
        for paper in self._papers.values():
            if paper.name == name:
                if not include_deleted and paper.deleted_at is not None:
                    return None
                return paper
        return None

    def list_all(self, include_deleted: bool = False) -> list[Paper]:
        """List all papers."""
        papers = [p for p in self._papers.values() if include_deleted or p.deleted_at is None]
        return sorted(papers, key=lambda p: p.name)

    def list_active(self) -> list[Paper]:
        """List only active papers."""
        papers = [p for p in self._papers.values() if p.deleted_at is None and p.is_active]
        return sorted(papers, key=lambda p: p.name)

    def update(
        self,
        paper_id: int,
        name: str | None = None,
        weight: int | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Paper | None:
        """Update paper information."""
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

        paper.updated_at = datetime.utcnow()
        return paper

    def soft_delete(self, paper_id: int) -> bool:
        """Soft delete a paper."""
        paper = self.get_by_id(paper_id, include_deleted=True)
        if not paper or paper.deleted_at is not None:
            return False

        paper.deleted_at = datetime.utcnow()
        paper.is_active = False
        return True

    def restore(self, paper_id: int) -> bool:
        """Restore a soft-deleted paper."""
        paper = self.get_by_id(paper_id, include_deleted=True)
        if not paper or paper.deleted_at is None:
            return False

        paper.deleted_at = None
        return True


class InMemoryFinishRepository(FinishRepository):
    """In-memory implementation of Finish repository with soft delete."""

    _next_id: int = 1

    def __init__(self):
        self._finishes: dict[int, Finish] = {}

    def _check_name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if finish name already exists."""
        for finish in self._finishes.values():
            if finish.name == name and finish.id != exclude_id:
                return True
        return False

    def create(
        self,
        name: str,
        finish_type: FinishType,
        unit: Unit,
        description: str | None = None,
    ) -> Finish:
        """Create a new finish."""
        if self._check_name_exists(name):
            raise ValueError(f"Finish with name '{name}' already exists")

        finish = Finish(
            id=InMemoryFinishRepository._next_id,
            name=name,
            finish_type=finish_type,
            unit=unit,
            description=description,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert finish.id is not None
        self._finishes[finish.id] = finish
        InMemoryFinishRepository._next_id += 1
        return finish

    def get_by_id(self, finish_id: int, include_deleted: bool = False) -> Finish | None:
        """Get finish by ID."""
        finish = self._finishes.get(finish_id)
        if finish and not include_deleted and finish.deleted_at is not None:
            return None
        return finish

    def get_by_name(self, name: str, include_deleted: bool = False) -> Finish | None:
        """Get finish by name."""
        for finish in self._finishes.values():
            if finish.name == name:
                if not include_deleted and finish.deleted_at is not None:
                    return None
                return finish
        return None

    def list_all(self, include_deleted: bool = False) -> list[Finish]:
        """List all finishes."""
        finishes = [f for f in self._finishes.values() if include_deleted or f.deleted_at is None]
        return sorted(finishes, key=lambda f: f.name)

    def list_active(self) -> list[Finish]:
        """List only active finishes."""
        finishes = [f for f in self._finishes.values() if f.deleted_at is None and f.is_active]
        return sorted(finishes, key=lambda f: f.name)

    def update(
        self,
        finish_id: int,
        name: str | None = None,
        finish_type: FinishType | None = None,
        unit: Unit | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Finish | None:
        """Update finish information."""
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

        finish.updated_at = datetime.utcnow()
        return finish

    def soft_delete(self, finish_id: int) -> bool:
        """Soft delete a finish."""
        finish = self.get_by_id(finish_id, include_deleted=True)
        if not finish or finish.deleted_at is not None:
            return False

        finish.deleted_at = datetime.utcnow()
        finish.is_active = False
        return True

    def restore(self, finish_id: int) -> bool:
        """Restore a soft-deleted finish."""
        finish = self.get_by_id(finish_id, include_deleted=True)
        if not finish or finish.deleted_at is None:
            return False

        finish.deleted_at = None
        return True
