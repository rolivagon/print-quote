"""MCP tool behavior over the in-memory test database."""

import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from quote.api.deps import get_current_user, get_db
from quote.api.main import app
from quote.domain.enums import ClientType, PlotterBillingMetric, UserRole
from quote.repo.models import Client, Paper, PlotterPricing, Quote, QuoteItem

FLYER = {
    "name": "Flyers",
    "print_type": "digital",
    "color_mode": "4/4",
    "quantity": 500,
    "width_cm": 10,
    "height_cm": 15,
}


@pytest.fixture
def mcp_db(seeded_db):
    db_session, seed = seeded_db

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    yield db_session, seed
    app.dependency_overrides.clear()


def _as(user):
    app.dependency_overrides[get_current_user] = lambda: user
    return user


def _seller():
    return SimpleNamespace(id=uuid.uuid4(), role=UserRole.VENDEDOR, is_active=True)


def _count(db_session, model) -> int:
    return db_session.execute(select(func.count()).select_from(model)).scalar_one()


def test_list_papers_and_finishes_match_digital_catalog(run_mcp, mcp_db):
    _, seed = mcp_db
    _as(seed["seller"])

    async def scenario(client):
        papers = await client.call_tool(
            "list_papers", {"print_type": "digital", "color_mode": "4/4"}
        )
        finishes = await client.call_tool("list_finishes", {"print_type": "digital"})
        offset_finishes = await client.call_tool("list_finishes", {"print_type": "offset"})
        return papers, finishes, offset_finishes

    papers, finishes, offset_finishes = run_mcp(scenario)

    assert [p["id"] for p in papers.structured_content["result"]] == [seed["paper"].id]
    assert "internal_costs" not in papers.structured_content["result"][0]
    assert [f["id"] for f in finishes.structured_content["result"]] == [seed["finish"].id]
    assert offset_finishes.structured_content["result"] == []


def test_list_clients_for_seller_returns_only_own_clients(run_mcp, mcp_db):
    db_session, seed = mcp_db
    seller = _as(_seller())
    own = Client(
        client_type=ClientType.COMPANY,
        tax_id="76.111.111-1",
        company_name="Own client",
        created_by_id=seller.id,
    )
    db_session.add(own)
    db_session.flush()

    async def scenario(client):
        return await client.call_tool("list_clients", {})

    result = run_mcp(scenario)

    assert [c["id"] for c in result.structured_content["result"]] == [own.id]


def test_preview_matches_created_quote_and_persists_nothing(run_mcp, mcp_db):
    db_session, seed = mcp_db
    _as(seed["seller"])
    item = {**FLYER, "paper_id": seed["paper"].id, "finishes": [seed["finish"].id]}

    async def preview(client):
        return await client.call_tool("preview_quote", {"items": [item]})

    preview_result = run_mcp(preview)
    assert not preview_result.is_error, preview_result.content
    assert _count(db_session, Quote) == 0
    assert _count(db_session, QuoteItem) == 0

    async def create(client):
        return await client.call_tool(
            "create_quote", {"client_id": seed["client"].id, "items": [item]}
        )

    created = run_mcp(create)
    assert not created.is_error, created.content

    previewed = preview_result.structured_content
    quote = created.structured_content
    assert quote["status"] == "draft"
    assert quote["seller_id"] == str(seed["seller"].id)
    assert (previewed["subtotal"], previewed["tax"], previewed["total"]) == (
        quote["subtotal"],
        quote["tax"],
        quote["total"],
    )
    assert previewed["items"][0]["total_final"] == quote["items"][0]["total_final"]
    assert previewed["items"][0]["sheets_needed"] == quote["items"][0]["sheets_needed"]
    assert _count(db_session, Quote) == 1


def test_create_quote_for_unknown_client_is_tool_error(run_mcp, mcp_db):
    db_session, seed = mcp_db
    _as(seed["seller"])
    item = {**FLYER, "paper_id": seed["paper"].id}

    async def scenario(client):
        return await client.call_tool("create_quote", {"client_id": 999999, "items": [item]})

    result = run_mcp(scenario)

    assert result.is_error
    assert "Client with ID 999999 not found" in result.content[0].text
    assert _count(db_session, Quote) == 0


def test_seller_cannot_create_quote_for_another_seller_client(run_mcp, mcp_db):
    db_session, seed = mcp_db
    _as(_seller())
    item = {**FLYER, "paper_id": seed["paper"].id}

    async def scenario(client):
        return await client.call_tool(
            "create_quote", {"client_id": seed["client"].id, "items": [item]}
        )

    result = run_mcp(scenario)

    assert result.is_error
    assert "Client access denied" in result.content[0].text
    assert _count(db_session, Quote) == 0


def test_preview_hides_internal_costs_from_sellers(run_mcp, mcp_db):
    _, seed = mcp_db
    item = {**FLYER, "paper_id": seed["paper"].id}

    async def scenario(client):
        return await client.call_tool("preview_quote", {"items": [item]})

    _as(_seller())
    seller_result = run_mcp(scenario)
    _as(seed["seller"])  # super admin
    admin_result = run_mcp(scenario)

    assert "internal_cost_breakdown" not in seller_result.structured_content["items"][0] or (
        seller_result.structured_content["items"][0]["internal_cost_breakdown"] is None
    )
    assert admin_result.structured_content["items"][0]["internal_cost_breakdown"] is not None


def test_plotter_preview_resolves_material_from_paper(run_mcp, mcp_db):
    db_session, seed = mcp_db
    _as(seed["seller"])
    material = Paper(name="Lona PVC", weight=440, is_active=True)
    db_session.add(material)
    db_session.flush()
    db_session.add(
        PlotterPricing(
            paper_id=material.id,
            billing_metric=PlotterBillingMetric.SQM,
            minimum=Decimal("0"),
            maximum=Decimal("1000"),
            unit_price=Decimal("10000"),
        )
    )
    db_session.flush()
    item = {
        "name": "Pendón",
        "print_type": "plotter",
        "quantity": 1,
        "width_cm": 100,
        "height_cm": 200,
        "paper_id": material.id,
    }

    async def scenario(client):
        papers = await client.call_tool("list_papers", {"print_type": "plotter"})
        preview = await client.call_tool("preview_quote", {"items": [item]})
        return papers, preview

    papers, preview = run_mcp(scenario)

    assert [p["id"] for p in papers.structured_content["result"]] == [material.id]
    assert not preview.is_error, preview.content
    previewed = preview.structured_content["items"][0]
    assert previewed["color_mode"] == "4/0"
    assert previewed["paper"]["name"] == "Lona PVC"
    assert previewed["material_cost"] != "$0"
