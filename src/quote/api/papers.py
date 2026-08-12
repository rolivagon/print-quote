"""Paper router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from quote.api.deps import get_current_user, get_db, require_admin
from quote.api.schemas import (
    Paper,
    PaperCreate,
    PaperPricing,
    PaperPricingCreate,
    PaperPricingUpdate,
    PaperUpdate,
)
from quote.domain.enums import ColorMode, PrintType
from quote.repo.models import User as UserModel
from quote.repo.sql_repo import SQLPaperRepository

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/", response_model=Paper, status_code=status.HTTP_201_CREATED)
def create_paper(
    db: Annotated[Session, Depends(get_db)],
    paper_in: PaperCreate,
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Create a new paper. Only admins can create papers."""
    paper_repo = SQLPaperRepository(db)
    try:
        return paper_repo.create(
            name=paper_in.name, weight=paper_in.weight, description=paper_in.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Paper])
def list_papers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    print_type: PrintType | None = None,
    color_mode: ColorMode | None = None,
    include_deleted: bool = False,
):
    """List all papers.

    Optionally filter by print_type and color_mode to get only papers
    that have pricing available for the specified criteria.
    """
    paper_repo = SQLPaperRepository(db)

    # Plotter materials use the separate plotter_pricing catalog and do not
    # have a color mode.
    if print_type == PrintType.PLOTTER:
        return paper_repo.get_plotter_papers()

    # If print_type and color_mode are provided, filter papers by availability
    if print_type is not None and color_mode is not None:
        return paper_repo.get_papers_by_color_mode(print_type, color_mode)

    return paper_repo.list_all(include_deleted=include_deleted)


@router.get("/{paper_id}", response_model=Paper)
def read_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get paper by ID."""
    paper_repo = SQLPaperRepository(db)
    paper = paper_repo.get_by_id(paper_id, include_deleted=True)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.patch("/{paper_id}", response_model=Paper)
def update_paper(
    paper_id: int,
    paper_in: PaperUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Update a paper. Only admins can update papers."""
    paper_repo = SQLPaperRepository(db)
    try:
        paper = paper_repo.update(paper_id, **paper_in.model_dump(exclude_unset=True))
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Soft delete a paper. Only admins can delete papers."""
    paper_repo = SQLPaperRepository(db)
    success = paper_repo.soft_delete(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found or already deleted")


# Pricing endpoints
@router.get("/{paper_id}/pricing", response_model=list[PaperPricing])
def list_paper_pricing(
    paper_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get all pricing entries for a paper."""
    paper_repo = SQLPaperRepository(db)
    paper = paper_repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper_repo.list_pricing(paper_id)


@router.post(
    "/{paper_id}/pricing", response_model=PaperPricing, status_code=status.HTTP_201_CREATED
)
def create_paper_pricing(
    paper_id: int,
    pricing_in: PaperPricingCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Create a new pricing entry for a paper. Only admins can create pricing."""
    paper_repo = SQLPaperRepository(db)
    paper = paper_repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    try:
        return paper_repo.create_pricing(
            paper_id=paper_id,
            print_type=pricing_in.print_type,
            min_quantity=pricing_in.min_quantity,
            max_quantity=pricing_in.max_quantity,
            unit_price=pricing_in.unit_price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/pricing/{pricing_id}", response_model=PaperPricing)
def update_paper_pricing(
    pricing_id: int,
    pricing_in: PaperPricingUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Update a paper pricing entry. Only admins can update pricing."""
    paper_repo = SQLPaperRepository(db)
    try:
        pricing = paper_repo.update_pricing(
            pricing_id,
            print_type=pricing_in.print_type,
            min_quantity=pricing_in.min_quantity,
            max_quantity=pricing_in.max_quantity,
            unit_price=pricing_in.unit_price,
        )
        if not pricing:
            raise HTTPException(status_code=404, detail="Pricing entry not found")
        return pricing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/pricing/{pricing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper_pricing(
    pricing_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Delete a paper pricing entry. Only admins can delete pricing."""
    paper_repo = SQLPaperRepository(db)
    success = paper_repo.delete_pricing(pricing_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pricing entry not found")
