"""Soft-deleted catalog entries stay visible in existing quotes but cannot be quoted again."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from quote.domain.enums import PlotterBillingMetric
from quote.repo.models import FinishPricing, Paper, PaperPricing, PlotterPricing


def _digital_payload(client_id: int, paper_id: int, finish_id: int) -> dict:
    return {
        "client_id": client_id,
        "items": [
            {
                "name": "Flyers",
                "print_type": "digital",
                "quantity": 500,
                "width_cm": 10.0,
                "height_cm": 15.0,
                "paper_id": paper_id,
                "color_mode": "4/4",
                "sheet_config": {"usable_width_cm": 31.0, "usable_height_cm": 46.0},
                "finishes": [finish_id],
                "loss_percentage": 0,
            }
        ],
    }


def _create_quote(client: TestClient, seed: dict) -> dict:
    response = client.post(
        "/api/quotes/",
        json=_digital_payload(
            seed["client_company"].id, seed["paper_couche"].id, seed["finish_cut"].id
        ),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_existing_quote_keeps_deleted_client_paper_and_finish(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    """Deleting catalog entries leaves previously created quotes intact."""
    _, seed = api_seeded_db
    quote = _create_quote(authorized_client, seed)

    for path in (
        f"/api/clients/{seed['client_company'].id}",
        f"/api/papers/{seed['paper_couche'].id}",
        f"/api/finishes/{seed['finish_cut'].id}",
    ):
        assert authorized_client.delete(path).status_code == 204

    response = authorized_client.get(f"/api/quotes/{quote['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["client"]["id"] == seed["client_company"].id
    specs = data["items"][0]["calculation_details"]["specifications"]
    assert specs["paper"]["name"] == seed["paper_couche"].name
    assert data["items"][0]["finishing_cost"] == quote["items"][0]["finishing_cost"]
    assert data["total"] == quote["total"]


def test_deleted_entries_are_hidden_from_listings(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    """Deleted clients and papers no longer appear in the selectors' listings."""
    _, seed = api_seeded_db
    client_id = seed["client_company"].id
    paper_id = seed["paper_couche"].id

    assert authorized_client.delete(f"/api/clients/{client_id}").status_code == 204
    assert authorized_client.delete(f"/api/papers/{paper_id}").status_code == 204

    clients = authorized_client.get("/api/clients/").json()
    papers = authorized_client.get("/api/papers/?print_type=digital&color_mode=4/4").json()
    assert client_id not in [client["id"] for client in clients]
    assert paper_id not in [paper["id"] for paper in papers]


def test_new_quote_rejects_deleted_client(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    _, seed = api_seeded_db
    authorized_client.delete(f"/api/clients/{seed['client_company'].id}")

    response = authorized_client.post(
        "/api/quotes/",
        json=_digital_payload(
            seed["client_company"].id, seed["paper_couche"].id, seed["finish_cut"].id
        ),
    )

    assert response.status_code == 404


def test_new_quote_rejects_deleted_paper(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    _, seed = api_seeded_db
    authorized_client.delete(f"/api/papers/{seed['paper_couche'].id}")

    response = authorized_client.post(
        "/api/quotes/",
        json=_digital_payload(
            seed["client_company"].id, seed["paper_couche"].id, seed["finish_cut"].id
        ),
    )

    assert response.status_code == 400
    assert "not available" in response.json()["detail"]


def test_new_quote_rejects_deleted_finish(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    _, seed = api_seeded_db
    authorized_client.delete(f"/api/finishes/{seed['finish_cut'].id}")

    response = authorized_client.post(
        "/api/quotes/",
        json=_digital_payload(
            seed["client_company"].id, seed["paper_couche"].id, seed["finish_cut"].id
        ),
    )

    assert response.status_code == 400
    assert "not available" in response.json()["detail"]


def test_deleting_paper_removes_its_price_ranges(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    """Paper price ranges go away with the paper; existing quotes keep their prices."""
    db_session, seed = api_seeded_db
    quote = _create_quote(authorized_client, seed)
    paper_id = seed["paper_couche"].id

    assert authorized_client.delete(f"/api/papers/{paper_id}").status_code == 204

    remaining = db_session.execute(
        select(PaperPricing).where(PaperPricing.paper_id == paper_id)
    ).all()
    assert remaining == []
    data = authorized_client.get(f"/api/quotes/{quote['id']}").json()
    assert data["items"][0]["paper_unit_price"] == quote["items"][0]["paper_unit_price"]


def test_deleting_finish_removes_its_price_ranges(
    authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
):
    db_session, seed = api_seeded_db
    finish_id = seed["finish_cut"].id

    assert authorized_client.delete(f"/api/finishes/{finish_id}").status_code == 204

    remaining = db_session.execute(
        select(FinishPricing).where(FinishPricing.finish_id == finish_id)
    ).all()
    assert remaining == []


def test_deleting_plotter_material_removes_its_catalog_rates(
    authorized_client: TestClient, api_test_state
):
    session = api_test_state.session
    paper = Paper(name="Vinilo eliminado", weight=1, is_active=True)
    session.add(paper)
    session.flush()
    session.add(
        PlotterPricing(
            paper_id=paper.id,
            minimum=Decimal("0"),
            maximum=Decimal("10"),
            billing_metric=PlotterBillingMetric.SQM,
            unit_price=Decimal("1000"),
        )
    )
    session.commit()

    assert authorized_client.delete(f"/api/papers/{paper.id}").status_code == 204

    remaining = session.execute(
        select(PlotterPricing).where(PlotterPricing.paper_id == paper.id)
    ).all()
    assert remaining == []
