"""SQL implementation of FixedProductRepository."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_
from sqlmodel import select

from quote.domain.models import FixedProduct as FixedProductDomain
from quote.domain.models import QuantityRange
from quote.repo.interfaces import FixedProductRepository
from quote.repo.models import FixedProduct, FixedProductQuantityRange


class SQLFixedProductRepository(FixedProductRepository):
    """SQL-based implementation of FixedProductRepository."""

    def __init__(self, session):
        """Initialize with database session.

        Args:
            session: SQLModel session
        """
        self._session = session

    def create(
        self,
        product_id: str,
        name: str,
        print_type: str,
        base_quote_snapshot: dict,
        client_id: int | None = None,
    ) -> FixedProduct:
        """Create a new fixed product without ranges."""
        product = FixedProduct(
            product_id=product_id,
            name=name,
            print_type=print_type,
            client_id=client_id,
            base_quote_snapshot=base_quote_snapshot,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        self._session.add(product)
        self._session.commit()
        self._session.refresh(product)
        return product

    def get_by_uuid(self, uuid: str) -> FixedProduct | None:
        """Get a fixed product by UUID."""
        statement = select(FixedProduct).where(FixedProduct.id == UUID(uuid))
        return self._session.execute(statement).scalars().first()

    def get_by_product_id(self, product_id: str) -> FixedProduct | None:
        """Get a fixed product by product_id (slug)."""
        statement = select(FixedProduct).where(FixedProduct.product_id == product_id)
        return self._session.execute(statement).scalars().first()

    def list_all(
        self, client_id: int | None = None, include_globals: bool = True
    ) -> list[FixedProduct]:
        """List all fixed products."""
        statement = select(FixedProduct).where(FixedProduct.is_active.is_(True))

        if client_id is not None:
            if include_globals:
                # Client-specific + global products
                statement = statement.where(
                    or_(FixedProduct.client_id == client_id, FixedProduct.client_id.is_(None))
                )
            else:
                # Only client-specific
                statement = statement.where(FixedProduct.client_id == client_id)
        else:
            # Only global products
            statement = statement.where(FixedProduct.client_id.is_(None))

        statement = statement.order_by(FixedProduct.name)
        return list(self._session.execute(statement).scalars().all())

    def add_range(
        self,
        product_uuid: str,
        min_quantity: int,
        max_quantity: int,
        unit_price: Decimal,
    ) -> FixedProductQuantityRange:
        """Add a quantity range to a fixed product."""
        # Check for overlap
        if self.check_range_overlap(product_uuid, min_quantity, max_quantity):
            raise ValueError(f"Range {min_quantity}-{max_quantity} overlaps with existing ranges")

        range_obj = FixedProductQuantityRange(
            fixed_product_id=UUID(product_uuid),
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            unit_price=unit_price,
            created_at=datetime.utcnow(),
        )
        self._session.add(range_obj)
        self._session.commit()
        self._session.refresh(range_obj)
        return range_obj

    def update_range(
        self,
        range_id: str,
        min_quantity: int | None = None,
        max_quantity: int | None = None,
        unit_price: Decimal | None = None,
    ) -> FixedProductQuantityRange | None:
        """Update a quantity range."""
        statement = select(FixedProductQuantityRange).where(
            FixedProductQuantityRange.id == UUID(range_id)
        )
        range_obj = self._session.execute(statement).scalars().first()

        if not range_obj:
            return None

        # Get new values or keep existing
        new_min = min_quantity if min_quantity is not None else range_obj.min_quantity
        new_max = max_quantity if max_quantity is not None else range_obj.max_quantity
        new_price = unit_price if unit_price is not None else range_obj.unit_price

        # Check for overlap (excluding this range)
        if self.check_range_overlap(
            str(range_obj.fixed_product_id), new_min, new_max, exclude_range_id=range_id
        ):
            raise ValueError(f"Range {new_min}-{new_max} overlaps with existing ranges")

        range_obj.min_quantity = new_min
        range_obj.max_quantity = new_max
        range_obj.unit_price = new_price

        self._session.add(range_obj)
        self._session.commit()
        self._session.refresh(range_obj)
        return range_obj

    def delete_range(self, range_id: str) -> bool:
        """Delete a quantity range."""
        statement = select(FixedProductQuantityRange).where(
            FixedProductQuantityRange.id == UUID(range_id)
        )
        range_obj = self._session.execute(statement).scalars().first()

        if not range_obj:
            return False

        self._session.delete(range_obj)
        self._session.commit()
        return True

    def delete(self, product_uuid: str) -> bool:
        """Delete a fixed product and all its ranges."""
        statement = select(FixedProduct).where(FixedProduct.id == UUID(product_uuid))
        product = self._session.execute(statement).scalars().first()

        if not product:
            return False

        self._session.delete(product)
        self._session.commit()
        return True

    def check_range_overlap(
        self,
        product_uuid: str,
        min_qty: int,
        max_qty: int,
        exclude_range_id: str | None = None,
    ) -> bool:
        """Check if a range overlaps with existing ranges."""
        statement = select(FixedProductQuantityRange).where(
            FixedProductQuantityRange.fixed_product_id == UUID(product_uuid)
        )

        if exclude_range_id:
            statement = statement.where(FixedProductQuantityRange.id != UUID(exclude_range_id))

        existing_ranges = self._session.execute(statement).scalars().all()

        for existing in existing_ranges:
            # Check overlap: A overlaps B if A starts before B ends AND B starts before A ends
            if min_qty <= existing.max_quantity and existing.min_quantity <= max_qty:
                return True

        return False

    def to_domain(self, product: FixedProduct) -> FixedProductDomain:
        """Convert SQL model to domain model.

        Args:
            product: SQL FixedProduct model

        Returns:
            Domain FixedProduct model
        """
        from quote.domain.models import QuoteBreakdown

        # Convert ranges
        quantity_ranges = [
            QuantityRange(
                min_qty=r.min_quantity,
                max_qty=r.max_quantity,
                unit_price=r.unit_price,
            )
            for r in product.ranges
        ]

        # Reconstruct QuoteBreakdown from snapshot
        snapshot = product.base_quote_snapshot
        base_quote = QuoteBreakdown(**snapshot)

        return FixedProductDomain(
            id=product.product_id,
            name=product.name,
            base_quote=base_quote,
            quantity_ranges=quantity_ranges,
            print_type=product.print_type,
            client_id=str(product.client_id) if product.client_id else None,
        )
