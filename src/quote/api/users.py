"""User router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from quote.api.deps import get_current_user, get_db, require_admin, require_super_admin
from quote.api.schemas import User, UserInvite, UserPasswordUpdate, UserUpdate
from quote.repo.models import User as UserModel
from quote.repo.sql_repo import SQLUserRepository
from quote.service.supabase_admin import SupabaseAdminError, invite_user, reset_password_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    db: Annotated[Session, Depends(get_db)],
    user_in: UserInvite,
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Invite a user through Supabase Auth. Only admins can invite users."""
    user_repo = SQLUserRepository(db)
    try:
        subject = invite_user(str(user_in.email), user_in.name)
        user = user_repo.get_by_id(subject, include_deleted=True)
        if user is None:
            raise HTTPException(status_code=503, detail="Invitation profile is not available")
        user = user_repo.update(subject, role=user_in.role)
        if user is None:
            raise HTTPException(status_code=503, detail="Invitation profile is not available")
        return user
    except (SupabaseAdminError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/me", response_model=User)
def read_user_me(current_user: Annotated[UserModel, Depends(get_current_user)]):
    """Get current user."""
    return current_user


@router.get("/", response_model=list[User])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
    include_deleted: bool = False,
):
    """List all users."""
    user_repo = SQLUserRepository(db)
    return user_repo.list_all(include_deleted=include_deleted)


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get user by ID."""
    user_repo = SQLUserRepository(db)
    user = user_repo.get_by_id(user_id, include_deleted=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=User)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Update a user. Only admins can update users."""
    user_repo = SQLUserRepository(db)

    update_data = user_in.model_dump(exclude_unset=True)
    try:
        user = user_repo.update(user_id, **update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{user_id}/password/", status_code=status.HTTP_204_NO_CONTENT)
def update_user_password(
    user_id: UUID,
    password_in: UserPasswordUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[UserModel, Depends(require_super_admin)],
):
    """Set a user's Auth password. Only super administrators can perform this action."""
    user_repo = SQLUserRepository(db)
    if user_repo.get_by_id(user_id, include_deleted=True) is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        reset_password_user(user_id, password_in.password)
    except SupabaseAdminError as exc:
        raise HTTPException(status_code=400, detail="Password update failed") from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    """Soft delete a user. Only admins can delete users."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )

    user_repo = SQLUserRepository(db)
    success = user_repo.soft_delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or already deleted")
