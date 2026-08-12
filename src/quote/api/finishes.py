"""Finish router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from quote.api.deps import get_current_user, get_db, require_admin
from quote.api.schemas import (
    Finish,
    FinishCreate,
    FinishPricing,
    FinishPricingCreate,
    FinishPricingUpdate,
    FinishUpdate,
)
from quote.domain.enums import PrintType
from quote.repo.models import User as UserModel
from quote.repo.sql_repo import SQLFinishRepository

router = APIRouter(prefix="/finishes", tags=["finishes"])


@router.post("/", response_model=Finish, status_code=status.HTTP_201_CREATED)
def create_finish(
    db: Annotated[Session, Depends(get_db)],
    finish_in: FinishCreate,
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Create a new finish. Only admins can create finishes."""
    finish_repo = SQLFinishRepository(db)
    try:
        return finish_repo.create(name=finish_in.name, description=finish_in.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Finish])
def list_finishes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    include_deleted: bool = False,
    print_type: PrintType | None = None,
):
    """List finishes, optionally restricted to a printing catalog."""
    finish_repo = SQLFinishRepository(db)
    if print_type == PrintType.PLOTTER:
        return finish_repo.get_plotter_finishes()
    return finish_repo.list_all(include_deleted=include_deleted)


@router.get("/{finish_id}", response_model=Finish)
def read_finish(
    finish_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get finish by ID."""
    finish_repo = SQLFinishRepository(db)
    finish = finish_repo.get_by_id(finish_id, include_deleted=True)
    if not finish:
        raise HTTPException(status_code=404, detail="Finish not found")
    return finish


@router.patch("/{finish_id}", response_model=Finish)
def update_finish(
    finish_id: int,
    finish_in: FinishUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Update a finish. Only admins can update finishes."""
    finish_repo = SQLFinishRepository(db)
    try:
        finish = finish_repo.update(finish_id, **finish_in.model_dump(exclude_unset=True))
        if not finish:
            raise HTTPException(status_code=404, detail="Finish not found")
        return finish
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{finish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finish(
    finish_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Soft delete a finish. Only admins can delete finishes."""
    finish_repo = SQLFinishRepository(db)
    success = finish_repo.soft_delete(finish_id)
    if not success:
        raise HTTPException(status_code=404, detail="Finish not found or already deleted")


# Pricing endpoints
@router.get("/{finish_id}/pricing", response_model=list[FinishPricing])
def list_finish_pricing(
    finish_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get all pricing entries for a finish."""
    finish_repo = SQLFinishRepository(db)
    finish = finish_repo.get_by_id(finish_id)
    if not finish:
        raise HTTPException(status_code=404, detail="Finish not found")
    return finish_repo.list_pricing(finish_id)


@router.post(
    "/{finish_id}/pricing", response_model=FinishPricing, status_code=status.HTTP_201_CREATED
)
def create_finish_pricing(
    finish_id: int,
    pricing_in: FinishPricingCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Create a new pricing entry for a finish. Only admins can create pricing."""
    finish_repo = SQLFinishRepository(db)
    finish = finish_repo.get_by_id(finish_id)
    if not finish:
        raise HTTPException(status_code=404, detail="Finish not found")

    try:
        return finish_repo.create_pricing(
            finish_id=finish_id,
            print_type=pricing_in.print_type,
            unit=pricing_in.unit,
            min_quantity=pricing_in.min_quantity,
            max_quantity=pricing_in.max_quantity,
            unit_price=pricing_in.unit_price,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/pricing/{pricing_id}", response_model=FinishPricing)
def update_finish_pricing(
    pricing_id: int,
    pricing_in: FinishPricingUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Update a finish pricing entry. Only admins can update pricing."""
    finish_repo = SQLFinishRepository(db)
    try:
        pricing = finish_repo.update_pricing(
            pricing_id,
            print_type=pricing_in.print_type,
            unit=pricing_in.unit,
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
def delete_finish_pricing(
    pricing_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Delete a finish pricing entry. Only admins can delete pricing."""
    finish_repo = SQLFinishRepository(db)
    success = finish_repo.delete_pricing(pricing_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pricing entry not found")
