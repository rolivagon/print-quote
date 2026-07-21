"""SQL repository for quotes."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from quote.domain.enums import ColorMode, PrintType, QuoteStatus
from quote.repo.interfaces import QuoteRepository
from quote.repo.models import Quote, QuoteItem, QuoteItemFinish


class SQLQuoteRepository(QuoteRepository):
    """SQL implementation of Quote repository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, quote: Quote) -> Quote:
        """Save a quote to the database.

        If the quote already exists (has an ID), it will be updated.
        Otherwise, it will be created.

        Args:
            quote: Quote to save

        Returns:
            Saved Quote instance
        """
        self._session.add(quote)
        self._session.commit()
        self._session.refresh(quote)
        return quote

    def create(
        self,
        quote_number: str,
        seller_id: UUID,
        client_id: int,
        subtotal: Decimal,
        tax: Decimal,
        total: Decimal,
        status: QuoteStatus = QuoteStatus.DRAFT,
    ) -> Quote:
        """Create a new quote.

        Args:
            quote_number: Unique quote number
            seller_id: User ID who created the quote
            client_id: Client ID
            subtotal: Subtotal amount
            tax: Tax amount
            total: Total amount
            status: Quote status (default: DRAFT)

        Returns:
            Created Quote instance
        """
        quote = Quote(
            quote_number=quote_number,
            seller_id=seller_id,
            client_id=client_id,
            subtotal=subtotal,
            tax=tax,
            total=total,
            status=status,
        )
        self._session.add(quote)
        self._session.commit()
        self._session.refresh(quote)
        return quote

    def add_item(
        self,
        quote_id: int,
        name: str,
        print_type: PrintType,
        color_mode: ColorMode,
        paper_id: int,
        width: Decimal,
        height: Decimal,
        quantity: int,
        paper_unit_price: Decimal,
        description: str | None = None,
        pieces_per_sheet: int | None = None,
        sheets_needed: int | None = None,
        total_sheets_with_merma: int | None = None,
        square_meters: Decimal | None = None,
        material_cost: Decimal | None = None,
        finishing_cost: Decimal | None = None,
        plates_cost: Decimal | None = None,
        run_cost: Decimal | None = None,
        fixed_costs: Decimal | None = None,
        paper_cost: Decimal | None = None,
        loss_percentage: float = 0,
        subtotal_before_losses: Decimal | None = None,
        subtotal_with_losses: Decimal | None = None,
        iva_amount: Decimal | None = None,
        total_final: Decimal | None = None,
        details_json: dict | None = None,
    ) -> QuoteItem:
        """Add an item to a quote with calculation details.

        Args:
            quote_id: Quote ID
            name: Item name
            print_type: Type of printing
            color_mode: Color mode
            paper_id: Paper ID
            width: Width
            height: Height
            quantity: Quantity
            paper_unit_price: Paper unit price at quote time
            description: Optional description
            pieces_per_sheet: Pieces per sheet
            sheets_needed: Sheets needed
            total_sheets_with_merma: Total sheets with waste
            square_meters: Square meters (plotter)
            material_cost: Material cost
            finishing_cost: Finishing cost
            plates_cost: Plates cost (offset)
            run_cost: Run cost (offset)
            fixed_costs: Fixed costs
            paper_cost: Paper cost
            loss_percentage: Loss percentage applied
            subtotal_before_losses: Subtotal before losses
            subtotal_with_losses: Subtotal after losses
            iva_amount: IVA amount
            total_final: Final total
            details_json: JSON snapshot of calculation details

        Returns:
            Created QuoteItem instance
        """
        item = QuoteItem(
            quote_id=quote_id,
            name=name,
            description=description,
            print_type=print_type,
            color_mode=color_mode,
            paper_id=paper_id,
            width=width,
            height=height,
            quantity=quantity,
            paper_unit_price=paper_unit_price,
            pieces_per_sheet=pieces_per_sheet,
            sheets_needed=sheets_needed,
            total_sheets_with_merma=total_sheets_with_merma,
            square_meters=square_meters,
            material_cost=material_cost or Decimal("0"),
            finishing_cost=finishing_cost or Decimal("0"),
            plates_cost=plates_cost or Decimal("0"),
            run_cost=run_cost or Decimal("0"),
            fixed_costs=fixed_costs or Decimal("0"),
            paper_cost=paper_cost or Decimal("0"),
            loss_percentage=loss_percentage,
            subtotal_before_losses=subtotal_before_losses or Decimal("0"),
            subtotal_with_losses=subtotal_with_losses or Decimal("0"),
            iva_amount=iva_amount or Decimal("0"),
            total_final=total_final or Decimal("0"),
            details_json=details_json,
        )
        self._session.add(item)
        self._session.commit()
        self._session.refresh(item)
        return item

    def add_item_finish(
        self,
        quote_item_id: int,
        finish_id: int,
        unit_price: Decimal,
    ) -> QuoteItemFinish:
        """Add a finish to a quote item.

        Args:
            quote_item_id: Quote item ID
            finish_id: Finish ID
            unit_price: Unit price at quote time

        Returns:
            Created QuoteItemFinish instance
        """
        item_finish = QuoteItemFinish(
            quote_item_id=quote_item_id,
            finish_id=finish_id,
            unit_price=unit_price,
        )
        self._session.add(item_finish)
        self._session.commit()
        self._session.refresh(item_finish)
        return item_finish

    def get_by_id(self, quote_id: int) -> Quote | None:
        """Get a quote by ID.

        Args:
            quote_id: Quote ID

        Returns:
            Quote if found, None otherwise
        """
        return self._session.get(Quote, quote_id)

    def get_by_id_with_items(self, quote_id: int) -> Quote | None:
        """Get a quote by ID with all related data (items, finishes, client).

        Args:
            quote_id: Quote ID

        Returns:
            Quote with all relationships loaded if found, None otherwise
        """
        statement = (
            select(Quote)
            .where(Quote.id == quote_id)
            .options(
                selectinload(Quote.client),
                selectinload(Quote.items).selectinload(QuoteItem.finishes),
                selectinload(Quote.items).selectinload(QuoteItem.paper),
            )
        )
        result = self._session.execute(statement)
        return result.scalar_one_or_none()

    def list_by_seller(
        self,
        seller_id: UUID,
        status: QuoteStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Quote]:
        """List quotes by seller.

        Args:
            seller_id: Seller/user ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of quotes
        """
        statement = select(Quote).where(Quote.seller_id == seller_id)

        if status:
            statement = statement.where(Quote.status == status)

        statement = statement.order_by(Quote.created_at.desc()).offset(skip).limit(limit)
        return list(self._session.execute(statement).scalars().all())

    def list_by_client(
        self,
        client_id: int,
        status: QuoteStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Quote]:
        """List quotes by client.

        Args:
            client_id: Client ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of quotes
        """
        statement = select(Quote).where(Quote.client_id == client_id)

        if status:
            statement = statement.where(Quote.status == status)

        statement = statement.order_by(Quote.created_at.desc()).offset(skip).limit(limit)
        return list(self._session.execute(statement).scalars().all())

    def list_all(
        self,
        status: QuoteStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Quote]:
        """List all quotes.

        Args:
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of quotes
        """
        statement = select(Quote)

        if status:
            statement = statement.where(Quote.status == status)

        statement = statement.order_by(Quote.created_at.desc()).offset(skip).limit(limit)
        return list(self._session.execute(statement).scalars().all())

    def update_status(self, quote_id: int, status: QuoteStatus) -> Quote | None:
        """Update quote status.

        Args:
            quote_id: Quote ID
            status: New status

        Returns:
            Updated Quote if found, None otherwise
        """
        quote = self.get_by_id(quote_id)
        if not quote:
            return None

        quote.status = status
        quote.updated_at = datetime.utcnow()

        if status == QuoteStatus.SENT:
            quote.sent_at = datetime.utcnow()

        self._session.commit()
        self._session.refresh(quote)
        return quote

    def generate_quote_number(self) -> str:
        """Generate a unique quote number.

        Returns:
            Unique quote number in format COT-YYYYMMDD-XXXX
        """
        today = datetime.utcnow()
        date_prefix = today.strftime("%Y%m%d")

        # Count quotes from today to generate sequential number
        statement = select(Quote).where(Quote.quote_number.like(f"COT-{date_prefix}-%"))
        count = len(self._session.execute(statement).scalars().all())

        sequential = str(count + 1).zfill(4)
        return f"COT-{date_prefix}-{sequential}"
