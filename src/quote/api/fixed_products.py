"""API router for Fixed Products."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from quote.api.deps import get_current_user, get_db, is_admin_role, require_admin
from quote.api.schemas import (
    FixedProductFromQuoteRequest,
    FixedProductListResponse,
    FixedProductQuoteResponse,
    FixedProductRangeCreate,
    FixedProductRangeResponse,
    FixedProductResponse,
    FixedProductSnapshot,
)
from quote.domain.enums import PrintType
from quote.repo.models import FixedProduct, User
from quote.repo.sql_fixed_product_repo import SQLFixedProductRepository

router = APIRouter(prefix="/fixed-products", tags=["fixed-products"])


def format_clp(amount: Decimal) -> str:
    """Format amount as Chilean Peso string."""
    return f"${amount:,.0f}".replace(",", ".")


def _convert_to_response(product: FixedProduct) -> FixedProductResponse:
    """Convert SQL model to API response."""
    snapshot_data = product.base_quote_snapshot

    return FixedProductResponse(
        id=str(product.id),
        product_id=product.product_id,
        name=product.name,
        print_type=product.print_type,
        client_id=product.client_id,
        snapshot=FixedProductSnapshot(
            reference_quantity=snapshot_data.get("quantity", 0),
            dimensions=snapshot_data.get("dimensions", {}),
            color_mode=snapshot_data.get("color_mode", ""),
            paper=snapshot_data.get("paper", {}),
            finishes=snapshot_data.get("finishes", []),
            pieces_per_sheet=snapshot_data.get("pieces_per_sheet"),
        ),
        ranges=[
            FixedProductRangeResponse(
                id=str(r.id),
                min_qty=r.min_quantity,
                max_qty=r.max_quantity,
                unit_price=format_clp(r.unit_price),
            )
            for r in product.ranges
        ],
        created_at=product.created_at,
    )


@router.post(
    "/from-quote", response_model=FixedProductResponse, status_code=status.HTTP_201_CREATED
)
def create_fixed_product_from_quote(
    request: FixedProductFromQuoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a fixed product from a quote calculation.

    The product is created without quantity ranges initially.
    Ranges must be added separately via POST /{id}/ranges.
    """
    # Create snapshot directly from request data (no calculation needed)
    snapshot = {
        "quantity": request.quote_data.quantity,
        "dimensions": {
            "width_cm": request.quote_data.dimensions.width_cm,
            "height_cm": request.quote_data.dimensions.height_cm,
        },
        "finishes": [],
        "pieces_per_sheet": None,
        "sheets_needed": None,
        "total_sheets_with_merma": None,
        "square_meters": None,
        "calculated_total": "0",
    }

    # Add type-specific fields
    print_type = request.quote_data.print_type
    if print_type in (PrintType.DIGITAL, PrintType.OFFSET):
        # For digital/offset, paper_id and color_mode are required
        snapshot["color_mode"] = (
            request.quote_data.color_mode.value
            if hasattr(request.quote_data.color_mode, "value")
            else str(request.quote_data.color_mode)
        )
        snapshot["paper"] = {"id": getattr(request.quote_data, "paper_id", None), "name": "Paper"}
        snapshot["sheet_config"] = {
            "usable_width_cm": getattr(request.quote_data.sheet_config, "usable_width_cm", 30),
            "usable_height_cm": getattr(request.quote_data.sheet_config, "usable_height_cm", 45),
        }
    elif print_type == PrintType.PLOTTER:
        # For plotter
        snapshot["material_type"] = getattr(request.quote_data, "material_type", "sintetico")
        snapshot["minimum_m2"] = getattr(request.quote_data, "minimum_m2", 0.5)

    # Create the fixed product
    repo = SQLFixedProductRepository(db)

    # Check if product_id already exists
    existing = repo.get_by_product_id(request.product_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product ID '{request.product_id}' already exists",
        )

    product = repo.create(
        product_id=request.product_id,
        name=request.name,
        print_type=print_type.value,
        base_quote_snapshot=snapshot,
        client_id=request.client_id,
    )

    return _convert_to_response(product)


@router.get("", response_model=FixedProductListResponse)
def list_fixed_products(
    client_id: int | None = Query(None, description="Filter by client ID"),
    include_globals: bool = Query(True, description="Include global products"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all fixed products.

    Returns global products (client_id=None) plus client-specific products
    if client_id is provided and include_globals is True.
    """
    repo = SQLFixedProductRepository(db)

    # If user is not admin, only show global products or their client's products
    if not is_admin_role(current_user.role):
        # For vendors, show global products only for now
        products = repo.list_all(client_id=None, include_globals=True)
    else:
        products = repo.list_all(client_id=client_id, include_globals=include_globals)

    return FixedProductListResponse(
        items=[_convert_to_response(p) for p in products],
        total=len(products),
    )


@router.get("/{product_id}", response_model=FixedProductResponse)
def get_fixed_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific fixed product by product_id (slug)."""
    repo = SQLFixedProductRepository(db)
    product = repo.get_by_product_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed product '{product_id}' not found",
        )

    # Check permissions
    if not is_admin_role(current_user.role) and product.client_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this product",
        )

    return _convert_to_response(product)


@router.post(
    "/{product_uuid}/ranges",
    response_model=FixedProductRangeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_range_to_product(
    product_uuid: str,
    range_data: FixedProductRangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Add a quantity range to a fixed product.

    Validates that the new range doesn't overlap with existing ranges.
    """
    repo = SQLFixedProductRepository(db)

    # Verify product exists
    product = repo.get_by_uuid(product_uuid)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed product '{product_uuid}' not found",
        )

    try:
        range_obj = repo.add_range(
            product_uuid=product_uuid,
            min_quantity=range_data.min_qty,
            max_quantity=range_data.max_qty,
            unit_price=range_data.unit_price,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return FixedProductRangeResponse(
        id=str(range_obj.id),
        min_qty=range_obj.min_quantity,
        max_qty=range_obj.max_quantity,
        unit_price=format_clp(range_obj.unit_price),
    )


@router.put("/{product_uuid}/ranges/{range_id}", response_model=FixedProductRangeResponse)
def update_range(
    product_uuid: str,
    range_id: str,
    range_data: FixedProductRangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update an existing quantity range.

    Validates that the updated range doesn't overlap with other ranges.
    """
    repo = SQLFixedProductRepository(db)

    try:
        range_obj = repo.update_range(
            range_id=range_id,
            min_quantity=range_data.min_qty,
            max_quantity=range_data.max_qty,
            unit_price=range_data.unit_price,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not range_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Range '{range_id}' not found",
        )

    return FixedProductRangeResponse(
        id=str(range_obj.id),
        min_qty=range_obj.min_quantity,
        max_qty=range_obj.max_quantity,
        unit_price=format_clp(range_obj.unit_price),
    )


@router.delete("/{product_uuid}/ranges/{range_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_range(
    product_uuid: str,
    range_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a quantity range from a fixed product."""
    repo = SQLFixedProductRepository(db)

    deleted = repo.delete_range(range_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Range '{range_id}' not found",
        )


@router.delete("/{product_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fixed_product(
    product_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a fixed product and all its ranges."""
    repo = SQLFixedProductRepository(db)

    deleted = repo.delete(product_uuid)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed product '{product_uuid}' not found",
        )


@router.get("/{product_uuid}/quote", response_model=FixedProductQuoteResponse)
def quote_with_fixed_product(
    product_uuid: str,
    quantity: int = Query(..., ge=1, description="Quantity to quote"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a quote using a fixed product.

    Calculates total based on quantity ranges.
    Returns error if quantity is not within any defined range.
    """
    repo = SQLFixedProductRepository(db)

    # Get product
    product = repo.get_by_uuid(product_uuid)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed product '{product_uuid}' not found",
        )

    # Check permissions
    if not is_admin_role(current_user.role) and product.client_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to quote this product",
        )

    # Find applicable range
    applicable_range = None
    for r in product.ranges:
        if r.min_quantity <= quantity <= r.max_quantity:
            applicable_range = r
            break

    if not applicable_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No price range found for quantity {quantity}",
        )

    # Calculate total
    total = Decimal(quantity) * applicable_range.unit_price

    return FixedProductQuoteResponse(
        product_id=product.product_id,
        product_name=product.name,
        quantity=quantity,
        applied_range=FixedProductRangeResponse(
            id=str(applicable_range.id),
            min_qty=applicable_range.min_quantity,
            max_qty=applicable_range.max_quantity,
            unit_price=format_clp(applicable_range.unit_price),
        ),
        unit_price=format_clp(applicable_range.unit_price),
        total_final=format_clp(total),
        reference_data={
            "pieces_per_sheet": product.base_quote_snapshot.get("pieces_per_sheet"),
            "reference_quantity": product.base_quote_snapshot.get("quantity"),
        },
    )
