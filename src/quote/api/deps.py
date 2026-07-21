"""Dependencies for the API."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from quote.domain.enums import UserRole
from quote.repo.database import SessionLocal
from quote.repo.models import User
from quote.repo.sql_repo import SQLUserRepository
from quote.service.security import InvalidAccessToken, validate_supabase_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


def is_admin_role(role: UserRole) -> bool:
    """Return whether a profile role has administrative access."""
    return role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Annotated[Session, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Get the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = validate_supabase_access_token(token)
        subject = UUID(payload["sub"])
    except (InvalidAccessToken, KeyError, ValueError) as exc:
        raise credentials_exception from exc

    user_repo = SQLUserRepository(db)
    user = user_repo.get_by_id(subject)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require admin or super admin role."""
    if not is_admin_role(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


def require_super_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require super admin role."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin privileges required"
        )
    return current_user
