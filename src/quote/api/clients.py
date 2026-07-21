"""Client router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from quote.api.deps import get_current_user, get_db
from quote.api.schemas import Client, ClientCreate, ClientUpdate
from quote.domain.enums import ClientType, UserRole
from quote.repo.models import Client as ClientModel
from quote.repo.models import User as UserModel
from quote.repo.sql_repo import SQLClientRepository

router = APIRouter(prefix="/clients", tags=["clients"])


def _can_manage_all_clients(user: UserModel) -> bool:
    """Only administrator profiles can access clients they did not create."""
    return user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}


def _get_permitted_client(
    db: Session, client_id: int, current_user: UserModel, include_deleted: bool = True
) -> ClientModel:
    """Load a client while enforcing its creator ownership."""
    client = SQLClientRepository(db).get_by_id(client_id, include_deleted=include_deleted)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if not _can_manage_all_clients(current_user) and client.created_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client access denied")
    return client


@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(
    db: Annotated[Session, Depends(get_db)],
    client_in: ClientCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Create a new client. Tracks the user who created the client."""
    client_repo = SQLClientRepository(db)
    try:
        if client_in.client_type == ClientType.INDIVIDUAL:
            if not client_in.first_name or not client_in.last_name:
                raise HTTPException(
                    status_code=400, detail="first_name and last_name are required for individuals"
                )
            return client_repo.create_individual(
                tax_id=client_in.tax_id,
                first_name=client_in.first_name,
                last_name=client_in.last_name,
                email=client_in.email,
                phone=client_in.phone,
                address=client_in.address,
                created_by_id=current_user.id,
            )
        else:
            if not client_in.company_name:
                raise HTTPException(
                    status_code=400, detail="company_name is required for companies"
                )
            return client_repo.create_company(
                tax_id=client_in.tax_id,
                company_name=client_in.company_name,
                email=client_in.email,
                phone=client_in.phone,
                address=client_in.address,
                created_by_id=current_user.id,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Client])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    include_deleted: bool = False,
):
    """List only owned clients unless the profile is an administrator."""
    statement = select(ClientModel)
    if not include_deleted:
        statement = statement.where(ClientModel.deleted_at.is_(None))
    if not _can_manage_all_clients(current_user):
        statement = statement.where(ClientModel.created_by_id == current_user.id)
    return list(
        db.execute(statement.order_by(ClientModel.first_name, ClientModel.company_name)).scalars()
    )


@router.get("/{client_id}", response_model=Client)
def read_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Get client by ID."""
    return _get_permitted_client(db, client_id, current_user)


@router.patch("/{client_id}", response_model=Client)
def update_client(
    client_id: int,
    client_in: ClientUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Update a client."""
    _get_permitted_client(db, client_id, current_user)
    client_repo = SQLClientRepository(db)
    client = client_repo.update(client_id, **client_in.model_dump(exclude_unset=True))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """Soft delete a client."""
    _get_permitted_client(db, client_id, current_user)
    client_repo = SQLClientRepository(db)
    success = client_repo.soft_delete(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found or already deleted")
