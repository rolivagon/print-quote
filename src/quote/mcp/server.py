"""MCP server exposing the quote creation flow of the quote view as tools."""

from collections.abc import AsyncIterator, Callable, Generator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.types import Receive, Scope, Send

from quote.api import clients, finishes, papers, quotes
from quote.api.deps import get_current_user, get_db
from quote.api.schemas import Client, QuoteCreateRequest, QuotePreviewResponse, QuoteResponse
from quote.domain.enums import ColorMode, PrintType
from quote.mcp.items import QuoteItemInput, normalize_item
from quote.repo.models import Paper as PaperModel
from quote.repo.models import User
from quote.repo.sql_repo import SQLFinishRepository

INSTRUCTIONS = """Cotizador de imprenta (digital, offset y plotter).

Flujo recomendado, igual que la vista de nueva cotización:
1. list_clients para obtener el client_id.
2. list_papers con el print_type (y color_mode para digital/offset) para elegir paper_id.
3. list_finishes con el print_type para elegir terminaciones (IDs).
4. preview_quote para revisar montos sin guardar.
5. create_quote para guardar la cotización en estado borrador (draft).
Los montos se expresan en CLP con IVA 19%."""

mcp = MCPServer(name="print-quote", title="Print Quote", instructions=INSTRUCTIONS)

_current_user: ContextVar[User] = ContextVar("mcp_current_user")
_db_provider: ContextVar[Callable[[], Generator[Session, None, None]]] = ContextVar(
    "mcp_db_provider"
)


class CatalogPaper(BaseModel):
    """Paper or plotter material available for quoting."""

    id: int
    name: str
    weight: int
    description: str | None = None


class CatalogFinish(BaseModel):
    """Finish available for quoting."""

    id: int
    name: str
    description: str | None = None


@contextmanager
def _request_session() -> Iterator[tuple[Session, User]]:
    """Open a session for the authenticated MCP request and translate API errors."""
    provider = _db_provider.get()()
    db = next(provider)
    try:
        yield db, _current_user.get()
    except HTTPException as exc:
        raise ToolError(str(exc.detail)) from exc
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        provider.close()


def _normalize_items(db: Session, items: list[QuoteItemInput]):
    def material_name(item: QuoteItemInput) -> str | None:
        if item.print_type != PrintType.PLOTTER or item.paper_id is None:
            return None
        paper = db.get(PaperModel, item.paper_id)
        return paper.name if paper else None

    return [normalize_item(item, material_name(item)) for item in items]


@mcp.tool()
def list_clients(
    search: Annotated[
        str | None, Field(description="Texto a buscar en nombre, empresa, RUT o email")
    ] = None,
) -> list[Client]:
    """Lista los clientes que el usuario puede cotizar (vendedores: solo los propios)."""
    with _request_session() as (db, user):
        return [
            Client.model_validate(client)
            for client in clients.list_clients(
                db=db, current_user=user, include_deleted=False, search=search
            )
        ]


@mcp.tool()
def list_papers(
    print_type: Annotated[PrintType, Field(description="digital, offset o plotter")],
    color_mode: Annotated[
        ColorMode | None, Field(description="4/0 o 4/4; requerido para digital y offset")
    ] = None,
) -> list[CatalogPaper]:
    """Lista papeles con precio para el tipo de impresión y modo de color (plotter: materiales)."""
    if print_type != PrintType.PLOTTER and color_mode is None:
        raise ToolError(f"color_mode is required for {print_type.value} papers")
    with _request_session() as (db, user):
        return [
            CatalogPaper.model_validate(paper, from_attributes=True)
            for paper in papers.list_papers(
                db=db, current_user=user, print_type=print_type, color_mode=color_mode
            )
        ]


@mcp.tool()
def list_finishes(
    print_type: Annotated[PrintType, Field(description="digital, offset o plotter")],
) -> list[CatalogFinish]:
    """Lista las terminaciones con precio para el tipo de impresión."""
    with _request_session() as (db, user):
        if print_type == PrintType.PLOTTER:
            catalog = finishes.list_finishes(db=db, current_user=user, print_type=print_type)
        else:
            catalog = SQLFinishRepository(db).get_finishes_by_print_type(print_type)
        return [CatalogFinish.model_validate(finish, from_attributes=True) for finish in catalog]


@mcp.tool()
def preview_quote(
    items: Annotated[list[QuoteItemInput], Field(min_length=1, description="Ítems a cotizar")],
) -> QuotePreviewResponse:
    """Calcula los montos de una cotización sin guardarla."""
    with _request_session() as (db, user):
        return quotes.build_quote_preview(db, _normalize_items(db, items), user)


@mcp.tool()
def create_quote(
    client_id: Annotated[int, Field(gt=0, description="ID del cliente (ver list_clients)")],
    items: Annotated[list[QuoteItemInput], Field(min_length=1, description="Ítems a cotizar")],
) -> QuoteResponse:
    """Crea y guarda la cotización en estado borrador (draft) a nombre del usuario."""
    with _request_session() as (db, user):
        request = QuoteCreateRequest(client_id=client_id, items=_normalize_items(db, items))
        return quotes.create_quote(db=db, request=request, current_user=user)


@asynccontextmanager
async def mcp_lifespan() -> AsyncIterator[None]:
    """Run a fresh stateless Streamable HTTP session manager for the application lifespan."""
    mcp.streamable_http_app(
        json_response=True,
        stateless_http=True,
        # Requests are authenticated with a bearer token; the public Cloud Run host varies.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    async with mcp.session_manager.run():
        yield


class _MCPResponse(Response):
    """Hand the untouched ASGI request to the MCP session manager."""

    def __init__(self) -> None:
        super().__init__()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await mcp.session_manager.handle_request(scope, receive, send)


router = APIRouter()


@router.api_route(
    "/mcp", methods=["GET", "POST", "DELETE"], include_in_schema=False, response_model=None
)
async def mcp_endpoint(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    """Authenticate with the Supabase bearer token, then serve the MCP request as that user.

    The endpoint is async so the context variables reach the session manager and the tools.
    GET and DELETE stay routed here so the SPA fallback never captures /mcp, but the stateless
    JSON server offers no SSE stream or session to terminate.
    """
    if request.method != "POST":
        return Response(status_code=405, headers={"Allow": "POST"})
    _current_user.set(current_user)
    _db_provider.set(request.app.dependency_overrides.get(get_db, get_db))
    return _MCPResponse()
