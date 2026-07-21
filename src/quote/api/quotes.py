"""Quote router for quote calculations and management."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quote.api.deps import get_current_user, get_db
from quote.api.schemas import (
    CalculationBreakdown,
    CalculationDetails,
    CostBreakdown,
    DigitalQuoteCalculate,
    Dimensions,
    DimensionsInfo,
    DirectCosts,
    FinalTotals,
    IvaInfo,
    LossesInfo,
    MarkupInfo,
    OffsetQuoteCalculate,
    OffsetSpecificCosts,
    PackingInfo,
    PaperInfo,
    PlotterQuoteCalculate,
    PricingCalculation,
    PricingInfo,
    ProductionCalculation,
    QuoteCreateRequest,
    QuoteFinishItem,
    QuoteItemResponse,
    QuoteResponse,
    QuoteStatusUpdate,
    Specifications,
)
from quote.api.utils import format_clp
from quote.domain.enums import PrintType, QuoteStatus, UserRole
from quote.pricing.digital import DigitalPricingStrategy
from quote.pricing.offset import OffsetPricingStrategy
from quote.pricing.packing import PackingCalculator
from quote.pricing.plotter import PlotterPricingStrategy
from quote.repo.models import User
from quote.repo.sql_quote_repo import SQLQuoteRepository
from quote.repo.sql_repo import SQLMasterRepository

router = APIRouter(prefix="/quotes", tags=["quotes"])


def _build_finishing_prices(
    db: Session,
    finishes: list[QuoteFinishItem],
    print_type: PrintType,
) -> dict:
    """Build finishing prices dict from database."""
    finishing_prices = {}
    master_repo = SQLMasterRepository(db)

    for finish_item in finishes:
        finish_pricing = master_repo.get_finish_price(
            finish_id=finish_item.finish_id,
            print_type=print_type,
            quantity=finish_item.quantity,
        )
        if finish_pricing:
            # Use the finish name as key
            from quote.repo.models import Finish

            finish = db.get(Finish, finish_item.finish_id)
            if finish:
                finishing_prices[finish.name] = {
                    "mode": finish_pricing.unit.value,
                    "price": finish_pricing.unit_price,
                }

    return finishing_prices


def _calculate_digital_quote(
    db: Session,
    data: DigitalQuoteCalculate,
) -> CalculationBreakdown:
    """Calculate digital printing quote following test_digital_user_case flow."""
    strategy = DigitalPricingStrategy()
    calculator = PackingCalculator()
    master_repo = SQLMasterRepository(db)

    # 1. Get paper price from database using SHEETS
    # First we need sheets_needed, but we need pieces_per_sheet first
    pieces_per_sheet = calculator.calculate_pieces_per_sheet(
        piece_width_cm=data.dimensions.width_cm,
        piece_height_cm=data.dimensions.height_cm,
        sheet_width_cm=data.sheet_config.usable_width_cm,
        sheet_height_cm=data.sheet_config.usable_height_cm,
        bleed_mm=data.geometry.bleed_mm,
        margin_mm=data.geometry.margin_mm,
        gap_mm=data.geometry.gap_mm,
        allow_rotate=data.geometry.allow_rotate,
    )

    # 2. Calculate sheets needed
    sheets_needed = int(calculator.calculate_sheets_needed(data.quantity, pieces_per_sheet))

    # 3. Get paper price for sheets_needed with color_mode
    paper_pricing = master_repo.get_paper_price(
        paper_id=data.paper_id,
        print_type=PrintType.DIGITAL,
        quantity=sheets_needed,
        color_mode=data.color_mode,
    )

    if not paper_pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No pricing found for paper ID {data.paper_id} with {sheets_needed} sheets",
        )

    # 4. Build price table with color_mode as key (like test)
    price_per_sheet = paper_pricing.unit_price
    color_config = (
        data.color_mode.value if hasattr(data.color_mode, "value") else str(data.color_mode)
    )
    price_table = {color_config: [(1, float("inf"), price_per_sheet)]}

    # 5. Calculate material cost: sheets_needed × price_per_sheet
    material_cost = strategy.calculate_sheet_cost(sheets_needed, color_config, price_table)

    # 6. Calculate finishing cost (like test)
    finishing_cost = Decimal("0")
    finishing_prices = {}
    for finish_item in data.finishes:
        finish_pricing = master_repo.get_finish_price(
            finish_id=finish_item.finish_id,
            print_type=PrintType.DIGITAL,
            quantity=data.quantity,
        )
        if finish_pricing:
            from quote.repo.models import Finish

            finish = db.get(Finish, finish_item.finish_id)
            if finish:
                finish_name = finish.name.lower().replace(" ", "_")
                finishing_prices[finish_name] = {
                    "mode": finish_pricing.unit.value,
                    "price": finish_pricing.unit_price,
                }
                finishing_cost += strategy.calculate_finishing_cost(
                    finishing_type=finish_name,
                    quantity=data.quantity,
                    finishing_prices=finishing_prices,
                )

    # 7. Subtotal: material_cost + finishing_cost
    subtotal = material_cost + finishing_cost

    # 8. Apply markup (0% base) + loss percentage
    markup_rate = Decimal("0")  # 0% base markup
    loss_rate = Decimal(str(data.loss_percentage)) / Decimal("100")
    total_markup_rate = markup_rate + loss_rate

    if total_markup_rate > 0:
        subtotal_with_markup = strategy.apply_markup(subtotal, total_markup_rate)
    else:
        subtotal_with_markup = subtotal

    markup_applied = subtotal_with_markup - subtotal

    # 9. Apply IVA (19%)
    iva_rate = Decimal("0.19")
    total_with_iva = strategy.apply_iva(subtotal_with_markup, iva_rate)

    # 10. Round to hundreds
    net_before_iva = strategy.round_to_hundreds(subtotal_with_markup)
    total_final = strategy.round_to_hundreds(total_with_iva)
    iva_amount = total_final - net_before_iva

    return CalculationBreakdown(
        pieces_per_sheet=pieces_per_sheet,
        sheets_needed=sheets_needed,
        total_sheets_with_merma=None,
        square_meters=None,
        billable_square_meters=None,
        material_cost=material_cost,
        finishing_cost=finishing_cost,
        plates_cost=Decimal("0"),
        run_cost=Decimal("0"),
        fixed_costs=Decimal("0"),
        paper_cost=Decimal("0"),
        subtotal_before_markup=subtotal,
        markup_applied=markup_applied,
        subtotal_with_markup=subtotal_with_markup,
        net_before_iva=net_before_iva,
        iva_amount=iva_amount,
        total_final=total_final,
    )


def _calculate_plotter_quote(
    db: Session,
    data: PlotterQuoteCalculate,
) -> CalculationBreakdown:
    """Calculate plotter printing quote following test_plotter_user_case flow."""
    strategy = PlotterPricingStrategy()
    master_repo = SQLMasterRepository(db)

    # 1. Get material price from database
    # For plotter, we need to map material_type to a paper or use default
    # First try to find paper by name matching material_type
    from quote.repo.models import Paper

    statement = select(Paper).where(func.lower(Paper.name).like(f"%{data.material_type.lower()}%"))
    paper = db.execute(statement).scalars().first()

    if paper:
        paper_pricing = master_repo.get_paper_price(
            paper_id=paper.id,
            print_type=PrintType.PLOTTER,
            quantity=data.quantity,
        )
    else:
        # Fallback: use any paper with plotter pricing
        papers = master_repo.get_all_active_papers()
        paper_pricing = None
        for p in papers:
            pricing = master_repo.get_paper_price(
                paper_id=p.id,
                print_type=PrintType.PLOTTER,
                quantity=data.quantity,
            )
            if pricing:
                paper_pricing = pricing
                break

    if not paper_pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No pricing found for material '{data.material_type}' with plotter",
        )

    # 2. Build price table with material_type as key
    price_m2 = paper_pricing.unit_price
    price_table = {data.material_type: price_m2}

    # 3. Calculate square meters per unit
    m2_unit = strategy.calculate_square_meters(
        data.dimensions.width_cm,
        data.dimensions.height_cm,
    )

    # 4. Apply minimum charge
    billable_m2 = strategy.apply_minimum_charge(m2_unit, Decimal(str(data.minimum_m2)))

    # 5. Calculate material cost per unit
    material_cost_unit = strategy.calculate_material_cost(
        billable_m2, data.material_type, price_table
    )

    # 6. Total material cost for quantity
    material_cost = material_cost_unit * data.quantity

    # 7. Calculate finishing cost with proper names
    finishing_cost = Decimal("0")
    finishing_prices = {}
    for finish_item in data.finishes:
        finish_pricing = master_repo.get_finish_price(
            finish_id=finish_item.finish_id,
            print_type=PrintType.PLOTTER,
            quantity=data.quantity,
        )
        if finish_pricing:
            from quote.repo.models import Finish

            finish = db.get(Finish, finish_item.finish_id)
            if finish:
                finish_name = finish.name.lower().replace(" ", "_")
                finishing_prices[finish_name] = {
                    "mode": finish_pricing.unit.value,
                    "price": finish_pricing.unit_price,
                }
                finishing_cost += strategy.calculate_finishing_cost(
                    finishing_type=finish_name,
                    quantity=data.quantity,
                    finishing_prices=finishing_prices,
                )

    # 8. Subtotal: material_cost + finishing_cost
    subtotal = material_cost + finishing_cost

    # 9. Apply markup (0% base) + loss percentage
    markup_rate = Decimal("0")  # 0% base markup
    loss_rate = Decimal(str(data.loss_percentage)) / Decimal("100")
    total_markup_rate = markup_rate + loss_rate

    if total_markup_rate > 0:
        subtotal_with_markup = strategy.apply_markup(subtotal, total_markup_rate)
    else:
        subtotal_with_markup = subtotal

    markup_applied = subtotal_with_markup - subtotal

    # 10. Apply IVA (19%)
    iva_rate = Decimal("0.19")
    total_with_iva = strategy.apply_iva(subtotal_with_markup, iva_rate)

    # 11. Round to hundreds
    net_before_iva = strategy.round_to_hundreds(subtotal_with_markup)
    total_final = strategy.round_to_hundreds(total_with_iva)
    iva_amount = total_final - net_before_iva

    return CalculationBreakdown(
        pieces_per_sheet=None,
        sheets_needed=None,
        total_sheets_with_merma=None,
        square_meters=float(m2_unit),
        billable_square_meters=float(billable_m2),
        material_cost=material_cost,
        finishing_cost=finishing_cost,
        plates_cost=Decimal("0"),
        run_cost=Decimal("0"),
        fixed_costs=Decimal("0"),
        paper_cost=Decimal("0"),
        subtotal_before_markup=subtotal,
        markup_applied=markup_applied,
        subtotal_with_markup=subtotal_with_markup,
        net_before_iva=net_before_iva,
        iva_amount=iva_amount,
        total_final=total_final,
    )


def _calculate_offset_quote(
    db: Session,
    data: OffsetQuoteCalculate,
) -> CalculationBreakdown:
    """Calculate offset printing quote."""
    strategy = OffsetPricingStrategy()
    calculator = PackingCalculator()

    # Get paper price from database
    master_repo = SQLMasterRepository(db)
    paper_pricing = master_repo.get_paper_price(
        paper_id=data.paper_id,
        print_type=PrintType.OFFSET,
        quantity=data.quantity,
    )

    if not paper_pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No pricing found for paper ID {data.paper_id} with quantity {data.quantity}",
        )

    # Build price table - for offset we need more complex pricing
    # For now, use simplified pricing structure
    price_per_sheet = paper_pricing.unit_price

    # Build offset price table
    price_table = {
        "planchas_por_color": Decimal("85000"),  # Default plate price per color
        "tiraje": {  # Run prices by quantity ranges
            1000: Decimal("150"),
            5000: Decimal("120"),
            10000: Decimal("100"),
            50000: Decimal("80"),
        },
        "terminaciones": {},  # Finishing prices
        "costos_fijos": {},  # Fixed costs
        "papel": {"default": price_per_sheet},
    }

    # Get finishing prices and add to table
    for finish_item in data.finishes:
        finish_pricing = master_repo.get_finish_price(
            finish_id=finish_item.finish_id,
            print_type=PrintType.OFFSET,
            quantity=data.quantity,
        )
        if finish_pricing:
            from quote.repo.models import Finish

            finish = db.get(Finish, finish_item.finish_id)
            if finish:
                price_table["terminaciones"][finish.name] = finish_pricing.unit_price

    # Calculate packing
    pieces_per_sheet = calculator.calculate_pieces_per_sheet(
        piece_width_cm=data.dimensions.width_cm,
        piece_height_cm=data.dimensions.height_cm,
        sheet_width_cm=data.sheet_config.usable_width_cm,
        sheet_height_cm=data.sheet_config.usable_height_cm,
        bleed_mm=data.geometry.bleed_mm,
        margin_mm=data.geometry.margin_mm,
        gap_mm=data.geometry.gap_mm,
        allow_rotate=data.geometry.allow_rotate,
    )

    # 3. Calculate total sheets with merma
    # Calculate quantity per design for proper sheet calculation
    quantity_per_design = (
        data.quantity // data.num_designs if data.num_designs > 0 else data.quantity
    )
    total_sheets = strategy.calculate_total_sheets_with_merma(
        quantity=quantity_per_design,
        pieces_per_sheet=pieces_per_sheet,
        merma_per_run=data.merma_per_design,
        num_runs=data.num_designs,
    )

    # 4. Calculate number of runs (2 tirajes for 16 designs = 8 designs per tiraje)
    num_runs = max(1, data.num_designs // 8)  # 8 designs per run

    # 5. Calculate plates cost: num_colors × price_per_color × num_runs
    # Default plates price: $7.000 per color (configurable via environment or settings)
    plates_price_per_color = Decimal("7000")
    color_config = (
        data.color_mode.value if hasattr(data.color_mode, "value") else str(data.color_mode)
    )
    plates_cost = strategy.calculate_plates_cost(
        color_config=color_config,
        price_per_color=plates_price_per_color,
        num_runs=num_runs,
    )

    # 6. Calculate run cost: price × num_runs
    # Default run price: $70.000 per run (configurable via environment or settings)
    run_price = Decimal("70000")
    run_cost = run_price * Decimal(num_runs)

    # 7. Calculate paper cost
    paper_cost = total_sheets * price_per_sheet

    # 8. Calculate finishing cost with proper names
    finishing_cost = Decimal("0")
    finishing_prices = {}
    for finish_item in data.finishes:
        finish_pricing = master_repo.get_finish_price(
            finish_id=finish_item.finish_id,
            print_type=PrintType.OFFSET,
            quantity=data.quantity,
        )
        if finish_pricing:
            from quote.repo.models import Finish

            finish = db.get(Finish, finish_item.finish_id)
            if finish:
                finish_name = finish.name.lower().replace(" ", "_")
                finishing_prices[finish_name] = {
                    "mode": finish_pricing.unit.value,
                    "price": finish_pricing.unit_price,
                }
                finishing_cost += strategy.calculate_finishing_cost(
                    finishing_type=finish_name,
                    quantity=data.quantity,
                    finishing_table=finishing_prices,
                )

    # 9. Calculate fixed costs (molde troquel, etc.)
    fixed_costs = Decimal("0")
    # TODO: Check if any finish requires fixed costs (e.g., troquel)

    # 10. Subtotal: sum of all costs
    subtotal = plates_cost + run_cost + paper_cost + finishing_cost + fixed_costs

    # 11. Apply markup (0% base) + loss percentage
    markup_rate = Decimal("0")  # 0% base markup
    loss_rate = Decimal(str(data.loss_percentage)) / Decimal("100")
    total_markup_rate = markup_rate + loss_rate

    if total_markup_rate > 0:
        subtotal_with_markup = strategy.apply_markup(subtotal, total_markup_rate)
    else:
        subtotal_with_markup = subtotal

    markup_applied = subtotal_with_markup - subtotal

    # 12. Apply IVA (19%)
    iva_rate = Decimal("0.19")
    total_with_iva = strategy.apply_iva(subtotal_with_markup, iva_rate)

    # 13. Round to hundreds
    net_before_iva = strategy.round_to_hundreds(subtotal_with_markup)
    total_final = strategy.round_to_hundreds(total_with_iva)
    iva_amount = total_final - net_before_iva

    return CalculationBreakdown(
        pieces_per_sheet=pieces_per_sheet,
        sheets_needed=total_sheets,
        total_sheets_with_merma=total_sheets,
        square_meters=None,
        billable_square_meters=None,
        material_cost=paper_cost,
        finishing_cost=finishing_cost,
        plates_cost=plates_cost,
        run_cost=run_cost,
        fixed_costs=fixed_costs,
        paper_cost=paper_cost,
        subtotal_before_markup=subtotal,
        markup_applied=markup_applied,
        subtotal_with_markup=subtotal_with_markup,
        net_before_iva=net_before_iva,
        iva_amount=iva_amount,
        total_final=total_final,
    )


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    db: Annotated[Session, Depends(get_db)],
    request: QuoteCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create and save a new quote with automatic calculation.

    The backend automatically calculates for each item:
    - pieces_per_sheet, sheets_needed
    - material_cost, finishing_cost
    - markup (by print type), IVA (19%), total_final

    The quote is created with DRAFT status.
    """
    from quote.repo.sql_repo import SQLClientRepository

    # Sellers can only quote their own clients; administrators retain global access.
    client_repo = SQLClientRepository(db)
    client = client_repo.get_by_id(request.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {request.client_id} not found",
        )
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        if client.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Client access denied"
            )

    # Process items and calculate
    quote_items = []
    total_subtotal = Decimal("0")
    total_tax = Decimal("0")
    total_final = Decimal("0")

    for item_data in request.items:
        # Build calculation data based on print type
        if item_data.print_type == PrintType.DIGITAL:
            calc_data = DigitalQuoteCalculate(
                print_type=item_data.print_type,
                quantity=item_data.quantity,
                dimensions=Dimensions(
                    width_cm=item_data.width_cm,
                    height_cm=item_data.height_cm,
                ),
                paper_id=item_data.paper_id,
                color_mode=item_data.color_mode,
                sheet_config=item_data.sheet_config,
                finishes=[QuoteFinishItem(finish_id=fid) for fid in item_data.finishes],
                loss_percentage=item_data.loss_percentage,
                vat_rate=19,
            )
            breakdown = _calculate_digital_quote(db, calc_data)

        elif item_data.print_type == PrintType.PLOTTER:
            calc_data = PlotterQuoteCalculate(
                print_type=item_data.print_type,
                quantity=item_data.quantity,
                dimensions=Dimensions(
                    width_cm=item_data.width_cm,
                    height_cm=item_data.height_cm,
                ),
                material_type=item_data.material_type or "sintetico",
                minimum_m2=item_data.minimum_m2 or 0.5,
                finishes=[QuoteFinishItem(finish_id=fid) for fid in item_data.finishes],
                loss_percentage=item_data.loss_percentage,
                vat_rate=19,
            )
            breakdown = _calculate_plotter_quote(db, calc_data)

        elif item_data.print_type == PrintType.OFFSET:
            calc_data = OffsetQuoteCalculate(
                print_type=item_data.print_type,
                quantity=item_data.quantity,
                dimensions=Dimensions(
                    width_cm=item_data.width_cm,
                    height_cm=item_data.height_cm,
                ),
                paper_id=item_data.paper_id,
                color_mode=item_data.color_mode,
                num_designs=item_data.num_designs,
                merma_per_design=item_data.merma_per_design,
                sheet_config=item_data.sheet_config,
                finishes=[QuoteFinishItem(finish_id=fid) for fid in item_data.finishes],
                loss_percentage=item_data.loss_percentage,
                vat_rate=19,
            )
            breakdown = _calculate_offset_quote(db, calc_data)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid print type: {item_data.print_type}",
            )

        # Get paper price for snapshot using sheets_needed, not quantity
        master_repo = SQLMasterRepository(db)
        sheets_for_pricing = (
            breakdown.sheets_needed if breakdown.sheets_needed else item_data.quantity
        )

        # Pass color_mode only for DIGITAL print type
        color_mode_for_pricing = (
            item_data.color_mode if item_data.print_type == PrintType.DIGITAL else None
        )

        paper_pricing = master_repo.get_paper_price(
            paper_id=item_data.paper_id,
            print_type=item_data.print_type,
            quantity=sheets_for_pricing,  # BUG FIX: Use sheets_needed for pricing
            color_mode=color_mode_for_pricing,
        )
        paper_unit_price = paper_pricing.unit_price if paper_pricing else Decimal("0")

        # Get paper name from database
        from quote.repo.models import Paper

        paper = db.get(Paper, item_data.paper_id)
        paper_name = paper.name if paper else None

        # Calculate individual finish costs with names
        finishes_info = []
        for finish_id in item_data.finishes:
            finish_pricing = master_repo.get_finish_price(
                finish_id=finish_id,
                print_type=item_data.print_type,
                quantity=item_data.quantity,
            )
            if finish_pricing:
                from quote.repo.models import Finish

                finish = db.get(Finish, finish_id)
                if finish:
                    # Calculate individual finish cost
                    finish_name = finish.name
                    unit_price = finish_pricing.unit_price
                    unit = finish_pricing.unit.value

                    # Calculate cost based on unit type
                    if unit == "job":
                        calculated_cost = unit_price
                    elif unit == "per_item":
                        calculated_cost = unit_price * Decimal(str(item_data.quantity))
                    elif unit == "per_1000":
                        calculated_cost = (
                            unit_price * Decimal(str(item_data.quantity)) / Decimal("1000")
                        )
                    elif unit == "sheet":
                        sheets = breakdown.sheets_needed or item_data.quantity
                        calculated_cost = unit_price * Decimal(str(sheets))
                    else:
                        calculated_cost = unit_price

                    finishes_info.append(
                        {
                            "id": finish_id,
                            "name": finish_name,
                            "unit_price": format_clp(unit_price),
                            "unit": unit,
                            "calculated_cost": format_clp(calculated_cost),
                        }
                    )

        # Build item data with calculation details
        quote_items.append(
            {
                "name": item_data.name,
                "description": item_data.description,
                "print_type": item_data.print_type,
                "color_mode": item_data.color_mode,
                "paper_id": item_data.paper_id,
                "width": Decimal(str(item_data.width_cm)),
                "height": Decimal(str(item_data.height_cm)),
                "quantity": item_data.quantity,
                "paper_unit_price": paper_unit_price,
                "pieces_per_sheet": breakdown.pieces_per_sheet,
                "sheets_needed": breakdown.sheets_needed,
                "total_sheets_with_merma": breakdown.total_sheets_with_merma,
                "square_meters": Decimal(str(breakdown.square_meters))
                if breakdown.square_meters
                else None,
                "material_cost": breakdown.material_cost,
                "finishing_cost": breakdown.finishing_cost,
                "plates_cost": breakdown.plates_cost,
                "run_cost": breakdown.run_cost,
                "fixed_costs": breakdown.fixed_costs,
                "paper_cost": breakdown.paper_cost,
                "loss_percentage": item_data.loss_percentage,
                "subtotal_before_losses": breakdown.subtotal_before_markup,
                "subtotal_with_losses": breakdown.subtotal_with_markup,
                "iva_amount": breakdown.iva_amount,
                "total_final": breakdown.total_final,
                # Extra data for details_json and response
                "paper_name": paper_name,
                "finishes_info": finishes_info,
            }
        )

        total_subtotal += breakdown.subtotal_with_markup
        total_tax += breakdown.iva_amount
        total_final += breakdown.total_final

    # Create quote
    quote_repo = SQLQuoteRepository(db)
    quote_number = quote_repo.generate_quote_number()

    quote = quote_repo.create(
        quote_number=quote_number,
        seller_id=current_user.id,
        client_id=request.client_id,
        subtotal=total_subtotal,
        tax=total_tax,
        total=total_final,
        status=QuoteStatus.DRAFT,
    )

    # Add items with calculation details
    for item in quote_items:
        # Build calculation details JSON snapshot
        calculation_details = {
            "specifications": {
                "print_type": (
                    item["print_type"].value
                    if hasattr(item["print_type"], "value")
                    else str(item["print_type"])
                ),
                "quantity": item["quantity"],
                "dimensions": {
                    "width_cm": float(item["width"]),
                    "height_cm": float(item["height"]),
                },
                "color_mode": (
                    item["color_mode"].value
                    if hasattr(item["color_mode"], "value")
                    else str(item["color_mode"])
                ),
                "paper": {
                    "id": item["paper_id"],
                    "name": item["paper_name"],
                },
                "finishes": item["finishes_info"],
            },
            "production_calculation": {
                "packing": {
                    "pieces_per_sheet": item["pieces_per_sheet"],
                    "sheets_needed": item["sheets_needed"],
                },
                "pricing": {
                    "paper_unit_price": float(item["paper_unit_price"]),
                    "currency": "CLP",
                },
            },
            "cost_breakdown": {
                "direct_costs": {
                    "material": format_clp(item["material_cost"]),
                    "finishing": format_clp(item["finishing_cost"]),
                    "total_direct_costs": format_clp(
                        item["material_cost"] + item["finishing_cost"]
                    ),
                },
                "offset_specific_costs": {
                    "plates": format_clp(item["plates_cost"]),
                    "printing_run": format_clp(item["run_cost"]),
                    "fixed_costs": format_clp(item["fixed_costs"]),
                },
            },
            "final_totals": {
                "subtotal_net": format_clp(item["subtotal_with_losses"]),
                "iva": {
                    "rate_percentage": 19.0,
                    "amount": format_clp(item["iva_amount"]),
                    "subtotal_with_iva": format_clp(
                        item["subtotal_with_losses"] + item["iva_amount"]
                    ),
                },
                "final_total_rounded": format_clp(item["total_final"]),
            },
        }

        quote_repo.add_item(
            quote_id=quote.id,
            name=item["name"],
            description=item["description"],
            print_type=item["print_type"],
            color_mode=item["color_mode"],
            paper_id=item["paper_id"],
            width=item["width"],
            height=item["height"],
            quantity=item["quantity"],
            paper_unit_price=item["paper_unit_price"],
            pieces_per_sheet=item["pieces_per_sheet"],
            sheets_needed=item["sheets_needed"],
            total_sheets_with_merma=item["total_sheets_with_merma"],
            square_meters=item["square_meters"],
            material_cost=item["material_cost"],
            finishing_cost=item["finishing_cost"],
            plates_cost=item["plates_cost"],
            run_cost=item["run_cost"],
            fixed_costs=item["fixed_costs"],
            paper_cost=item["paper_cost"],
            loss_percentage=item["loss_percentage"],
            subtotal_before_losses=item["subtotal_before_losses"],
            subtotal_with_losses=item["subtotal_with_losses"],
            iva_amount=item["iva_amount"],
            total_final=item["total_final"],
            details_json=calculation_details,
        )

        # Add finishes to the item
        for finish_info in item["finishes_info"]:
            # Parse formatted price back to Decimal
            price_str = finish_info["unit_price"].replace("$", "").replace(".", "")
            unit_price = Decimal(price_str.replace(",", "."))
            quote_repo.add_item_finish(
                quote_item_id=quote.items[-1].id if quote.items else None,
                finish_id=finish_info["id"],
                unit_price=unit_price,
            )

    # Refresh quote with items
    db.refresh(quote)

    # Build items response with calculation details
    items_response = []
    for item in quote.items:
        # Build nested calculation details
        calculation_details = CalculationDetails(
            specifications=Specifications(
                print_type=item.print_type,
                quantity=item.quantity,
                dimensions=DimensionsInfo(
                    width_cm=item.width,
                    height_cm=item.height,
                ),
                color_mode=item.color_mode,
                paper=PaperInfo(
                    id=item.paper_id,
                    name=None,  # Could fetch from DB if needed
                ),
            ),
            production_calculation=ProductionCalculation(
                packing=PackingInfo(
                    pieces_per_sheet=item.pieces_per_sheet,
                    sheets_needed=item.sheets_needed,
                ),
                pricing=PricingInfo(
                    paper_unit_price=item.paper_unit_price,
                    currency="CLP",
                ),
            ),
            cost_breakdown=CostBreakdown(
                direct_costs=DirectCosts(
                    material=format_clp(item.material_cost),
                    finishing=format_clp(item.finishing_cost),
                    total_direct_costs=format_clp(item.material_cost + item.finishing_cost),
                ),
                offset_specific_costs=OffsetSpecificCosts(
                    plates=format_clp(item.plates_cost),
                    printing_run=format_clp(item.run_cost),
                    fixed_costs=format_clp(item.fixed_costs),
                ),
            ),
            pricing_calculation=PricingCalculation(
                markup=MarkupInfo(
                    rate_percentage=50.0,  # Digital default
                    amount=format_clp(item.subtotal_with_losses - item.subtotal_before_losses),
                    base_amount=format_clp(item.subtotal_before_losses),
                    subtotal_with_markup=format_clp(item.subtotal_with_losses),
                ),
                losses=LossesInfo(
                    percentage=item.loss_percentage,
                    amount=format_clp(
                        item.subtotal_before_losses
                        * Decimal(str(item.loss_percentage))
                        / Decimal("100")
                    ),
                ),
            ),
            final_totals=FinalTotals(
                subtotal_net=format_clp(item.subtotal_with_losses),
                iva=IvaInfo(
                    rate_percentage=19.0,
                    amount=format_clp(item.iva_amount),
                    subtotal_with_iva=format_clp(item.subtotal_with_losses + item.iva_amount),
                ),
                final_total_rounded=format_clp(item.total_final),
            ),
        )

        items_response.append(
            QuoteItemResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                calculation_details=calculation_details,
                # Legacy fields for backward compatibility
                print_type=item.print_type,
                color_mode=item.color_mode,
                paper_id=item.paper_id,
                width=item.width,
                height=item.height,
                quantity=item.quantity,
                paper_unit_price=format_clp(item.paper_unit_price),
                pieces_per_sheet=item.pieces_per_sheet,
                sheets_needed=item.sheets_needed,
                total_sheets_with_merma=item.total_sheets_with_merma,
                square_meters=item.square_meters,
                material_cost=format_clp(item.material_cost),
                finishing_cost=format_clp(item.finishing_cost),
                plates_cost=format_clp(item.plates_cost),
                run_cost=format_clp(item.run_cost),
                fixed_costs=format_clp(item.fixed_costs),
                paper_cost=format_clp(item.paper_cost),
                loss_percentage=item.loss_percentage,
                subtotal_before_losses=format_clp(item.subtotal_before_losses),
                subtotal_with_losses=format_clp(item.subtotal_with_losses),
                iva_amount=format_clp(item.iva_amount),
                total_final=format_clp(item.total_final),
            )
        )

    # Build client response
    from quote.api.schemas import Client

    client_response = Client(
        id=client.id,
        tax_id=client.tax_id,
        client_type=client.client_type,
        first_name=client.first_name,
        last_name=client.last_name,
        company_name=client.company_name,
        email=client.email,
        phone=client.phone,
        address=client.address,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )

    return QuoteResponse(
        id=quote.id,
        quote_number=quote.quote_number,
        status=quote.status,
        seller_id=quote.seller_id,
        client_id=quote.client_id,
        client=client_response,
        subtotal=format_clp(quote.subtotal),
        tax=format_clp(quote.tax),
        total=format_clp(quote.total),
        items=items_response,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a quote by ID with full details including items."""
    quote_repo = SQLQuoteRepository(db)
    quote = quote_repo.get_by_id_with_items(quote_id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with ID {quote_id} not found",
        )

    # Check permissions
    from quote.domain.enums import UserRole

    if (
        current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        and quote.seller_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own quotes",
        )

    # Build items response with calculation details
    items_response = []
    for item in quote.items:
        # Build nested calculation details
        calculation_details = CalculationDetails(
            specifications=Specifications(
                print_type=item.print_type,
                quantity=item.quantity,
                dimensions=DimensionsInfo(
                    width_cm=item.width,
                    height_cm=item.height,
                ),
                color_mode=item.color_mode,
                paper=PaperInfo(
                    id=item.paper_id,
                    name=item.paper.name if item.paper else None,
                ),
            ),
            production_calculation=ProductionCalculation(
                packing=PackingInfo(
                    pieces_per_sheet=item.pieces_per_sheet,
                    sheets_needed=item.sheets_needed,
                ),
                pricing=PricingInfo(
                    paper_unit_price=item.paper_unit_price,
                    currency="CLP",
                ),
            ),
            cost_breakdown=CostBreakdown(
                direct_costs=DirectCosts(
                    material=format_clp(item.material_cost),
                    finishing=format_clp(item.finishing_cost),
                    total_direct_costs=format_clp(item.material_cost + item.finishing_cost),
                ),
                offset_specific_costs=OffsetSpecificCosts(
                    plates=format_clp(item.plates_cost),
                    printing_run=format_clp(item.run_cost),
                    fixed_costs=format_clp(item.fixed_costs),
                ),
            ),
            pricing_calculation=PricingCalculation(
                markup=MarkupInfo(
                    rate_percentage=50.0,
                    amount=format_clp(item.subtotal_with_losses - item.subtotal_before_losses),
                    base_amount=format_clp(item.subtotal_before_losses),
                    subtotal_with_markup=format_clp(item.subtotal_with_losses),
                ),
                losses=LossesInfo(
                    percentage=item.loss_percentage,
                    amount=format_clp(
                        item.subtotal_before_losses
                        * Decimal(str(item.loss_percentage))
                        / Decimal("100")
                    ),
                ),
            ),
            final_totals=FinalTotals(
                subtotal_net=format_clp(item.subtotal_with_losses),
                iva=IvaInfo(
                    rate_percentage=19.0,
                    amount=format_clp(item.iva_amount),
                    subtotal_with_iva=format_clp(item.subtotal_with_losses + item.iva_amount),
                ),
                final_total_rounded=format_clp(item.total_final),
            ),
        )

        items_response.append(
            QuoteItemResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                calculation_details=calculation_details,
                print_type=item.print_type,
                color_mode=item.color_mode,
                paper_id=item.paper_id,
                width=item.width,
                height=item.height,
                quantity=item.quantity,
                paper_unit_price=format_clp(item.paper_unit_price),
                pieces_per_sheet=item.pieces_per_sheet,
                sheets_needed=item.sheets_needed,
                total_sheets_with_merma=item.total_sheets_with_merma,
                square_meters=item.square_meters,
                material_cost=format_clp(item.material_cost),
                finishing_cost=format_clp(item.finishing_cost),
                plates_cost=format_clp(item.plates_cost),
                run_cost=format_clp(item.run_cost),
                fixed_costs=format_clp(item.fixed_costs),
                paper_cost=format_clp(item.paper_cost),
                loss_percentage=item.loss_percentage,
                subtotal_before_losses=format_clp(item.subtotal_before_losses),
                subtotal_with_losses=format_clp(item.subtotal_with_losses),
                iva_amount=format_clp(item.iva_amount),
                total_final=format_clp(item.total_final),
            )
        )

    # Build client response
    from quote.api.schemas import Client

    client_response = None
    if quote.client:
        client_response = Client(
            id=quote.client.id,
            tax_id=quote.client.tax_id,
            client_type=quote.client.client_type,
            first_name=quote.client.first_name,
            last_name=quote.client.last_name,
            company_name=quote.client.company_name,
            email=quote.client.email,
            phone=quote.client.phone,
            address=quote.client.address,
            created_at=quote.client.created_at,
            updated_at=quote.client.updated_at,
        )

    return QuoteResponse(
        id=quote.id,
        quote_number=quote.quote_number,
        status=quote.status,
        seller_id=quote.seller_id,
        client_id=quote.client_id,
        client=client_response,
        subtotal=format_clp(quote.subtotal),
        tax=format_clp(quote.tax),
        total=format_clp(quote.total),
        items=items_response,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
    )


@router.patch("/{quote_id}/status", response_model=QuoteResponse)
def update_quote_status(
    quote_id: int,
    status_update: QuoteStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update quote status.

    Allowed transitions:
    - DRAFT -> SENT: Send quote to client
    - SENT -> APPROVED: Client approved the quote
    - SENT -> REJECTED: Client rejected the quote
    """
    quote_repo = SQLQuoteRepository(db)
    quote = quote_repo.get_by_id(quote_id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with ID {quote_id} not found",
        )

    # Check permissions
    from quote.domain.enums import UserRole

    if (
        current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        and quote.seller_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own quotes",
        )

    # Validate status transition
    valid_transitions = {
        QuoteStatus.DRAFT: [QuoteStatus.SENT],
        QuoteStatus.SENT: [QuoteStatus.APPROVED, QuoteStatus.REJECTED],
        QuoteStatus.APPROVED: [],
        QuoteStatus.REJECTED: [],
    }

    if status_update.status not in valid_transitions.get(quote.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {quote.status.value} to {status_update.status.value}",
        )

    updated_quote = quote_repo.update_status(quote_id, status_update.status)

    return QuoteResponse(
        id=updated_quote.id,
        quote_number=updated_quote.quote_number,
        status=updated_quote.status,
        seller_id=updated_quote.seller_id,
        client_id=updated_quote.client_id,
        client=None,
        subtotal=format_clp(updated_quote.subtotal),
        tax=format_clp(updated_quote.tax),
        total=format_clp(updated_quote.total),
        items=[],
        created_at=updated_quote.created_at,
        updated_at=updated_quote.updated_at,
    )
