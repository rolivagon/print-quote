"""API coverage for internal-cost administration and authorization."""

from fastapi.testclient import TestClient

from quote.api.deps import get_current_user
from quote.api.main import app
from quote.domain.enums import ColorMode, PlotterBillingMetric, PrintType, Unit
from quote.repo.models import (
    Finish,
    FinishInternalCost,
    PaperInternalCost,
    PaperPricing,
    PlotterPricing,
    QuoteItem,
)


def test_admin_can_create_and_update_paper_internal_costs(authorized_client: TestClient):
    response = authorized_client.post(
        "/api/papers/",
        json={
            "name": "API internal paper",
            "weight": 300,
            "internal_costs": [
                {
                    "print_type": "digital",
                    "unit": "sheet",
                    "paper_cost": "0",
                    "printing_cost": "1.25",
                },
                {"print_type": "plotter", "unit": "sqm", "paper_cost": "2.50"},
            ],
        },
    )

    assert response.status_code == 201
    paper_id = response.json()["id"]
    update = authorized_client.patch(
        f"/api/papers/{paper_id}",
        json={
            "internal_costs": [
                {"print_type": "digital", "unit": "sheet", "paper_cost": "0", "printing_cost": "0"}
            ]
        },
    )

    assert update.status_code == 200
    assert update.json()["internal_costs"][0]["paper_cost"] == "0.00"
    assert update.json()["internal_costs"][0]["printing_cost"] == "0.00"


def test_invalid_internal_cost_rows_are_rejected(authorized_client: TestClient):
    response = authorized_client.post(
        "/api/papers/",
        json={
            "name": "Invalid internal paper",
            "weight": 300,
            "internal_costs": [{"print_type": "plotter", "unit": "sheet", "paper_cost": "0"}],
        },
    )
    assert response.status_code == 422

    future_unit = authorized_client.post(
        "/api/finishes/",
        json={
            "name": "Future finish unit",
            "internal_costs": [{"print_type": "plotter", "unit": "sqm", "unit_cost": "1"}],
        },
    )
    assert future_unit.status_code == 422


def test_future_finish_units_are_rejected_on_create_and_update(
    authorized_client: TestClient, api_test_state
):
    future_units = ("sqm", "job", "per_item", "per_1000")
    attempted_names = [f"Future finish create {index}" for index in range(len(future_units))]

    for name, unit in zip(attempted_names, future_units, strict=False):
        response = authorized_client.post(
            "/api/finishes/",
            json={
                "name": name,
                "internal_costs": [{"print_type": "plotter", "unit": unit, "unit_cost": "1"}],
            },
        )
        assert response.status_code == 422, response.text

    assert (
        api_test_state.session.query(Finish).filter(Finish.name.in_(attempted_names)).count() == 0
    )

    created = authorized_client.post(
        "/api/finishes/",
        json={
            "name": "Valid finish for future-unit update",
            "internal_costs": [{"print_type": "plotter", "unit": "sheet", "unit_cost": "1"}],
        },
    )
    assert created.status_code == 201, created.text
    finish_id = created.json()["id"]

    for unit in future_units:
        response = authorized_client.patch(
            f"/api/finishes/{finish_id}",
            json={"internal_costs": [{"print_type": "plotter", "unit": unit, "unit_cost": "2"}]},
        )
        assert response.status_code == 422, response.text

    rows = (
        api_test_state.session.query(FinishInternalCost)
        .filter(FinishInternalCost.finish_id == finish_id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].finish_id == finish_id
    assert rows[0].unit == Unit.SHEET


def test_non_admin_cannot_create_internal_cost_catalog(api_client: TestClient, api_test_user):
    app.dependency_overrides[get_current_user] = lambda: api_test_user
    api_client.headers = {"Authorization": "Bearer test-supabase-token"}
    response = api_client.post(
        "/api/finishes/",
        json={
            "name": "Seller internal finish",
            "internal_costs": [{"print_type": "plotter", "unit": "sheet", "unit_cost": "0"}],
        },
    )

    assert response.status_code == 403


def test_quote_response_contains_historical_internal_snapshot(
    authorized_client: TestClient, api_seeded_db
):
    db_session, seed_data = api_seeded_db
    paper = seed_data["paper_couche"]
    client = seed_data["client_company"]
    db_session.add(
        PaperInternalCost(
            paper_id=paper.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.SHEET,
            paper_cost=0,
            printing_cost=2,
        )
    )
    db_session.commit()
    response = authorized_client.post(
        "/api/quotes/",
        json={
            "client_id": client.id,
            "items": [
                {
                    "name": "Snapshot item",
                    "print_type": "digital",
                    "quantity": 10,
                    "width_cm": 10,
                    "height_cm": 15,
                    "paper_id": paper.id,
                    "color_mode": "4/4",
                    "sheet_config": {"usable_width_cm": 31, "usable_height_cm": 46},
                }
            ],
        },
    )

    assert response.status_code == 201
    item = response.json()["items"][0]
    snapshot = item["internal_cost_breakdown"]
    assert snapshot["paper"] == "$0"
    assert snapshot["printing"] != "$0"
    assert snapshot["total"] != "$0"
    stored_item = db_session.query(QuoteItem).filter_by(quote_id=response.json()["id"]).one()
    assert stored_item.internal_cost_snapshot["configured_rates"]["paper"]["printing_cost"] in {
        "2",
        "2.00",
    }


def test_digital_internal_cost_uses_consumed_sheets_and_preserves_zero(
    authorized_client: TestClient, api_seeded_db
):
    db_session, seed_data = api_seeded_db
    db_session.add(
        PaperInternalCost(
            paper_id=seed_data["paper_couche"].id,
            print_type=PrintType.DIGITAL,
            unit=Unit.SHEET,
            paper_cost=0,
            printing_cost=3,
        )
    )
    db_session.commit()
    response = authorized_client.post(
        "/api/quotes/",
        json={
            "client_id": seed_data["client_company"].id,
            "items": [
                {
                    "name": "Digital internal metric",
                    "print_type": "digital",
                    "quantity": 500,
                    "width_cm": 10,
                    "height_cm": 15,
                    "paper_id": seed_data["paper_couche"].id,
                    "color_mode": "4/4",
                    "sheet_config": {"usable_width_cm": 31, "usable_height_cm": 46},
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    item = response.json()["items"][0]
    assert item["internal_cost_breakdown"]["paper"] == "$0"
    assert item["internal_cost_breakdown"]["printing"] != "no indicado"


def test_offset_internal_cost_includes_merma_sheets(authorized_client: TestClient, api_seeded_db):
    db_session, seed_data = api_seeded_db
    db_session.add_all(
        [
            PaperPricing(
                paper_id=seed_data["paper_couche"].id,
                print_type=PrintType.OFFSET,
                color_mode=ColorMode.C4_0,
                min_quantity=1,
                unit_price=1,
            ),
            PaperInternalCost(
                paper_id=seed_data["paper_couche"].id,
                print_type=PrintType.OFFSET,
                unit=Unit.SHEET,
                paper_cost=2,
                printing_cost=0,
            ),
        ]
    )
    db_session.commit()
    response = authorized_client.post(
        "/api/quotes/",
        json={
            "client_id": seed_data["client_company"].id,
            "items": [
                {
                    "name": "Offset internal metric",
                    "print_type": "offset",
                    "quantity": 100,
                    "width_cm": 10,
                    "height_cm": 15,
                    "paper_id": seed_data["paper_couche"].id,
                    "color_mode": "4/0",
                    "num_designs": 1,
                    "merma_per_design": 3,
                    "sheet_config": {"usable_width_cm": 70, "usable_height_cm": 50},
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    item = response.json()["items"][0]
    stored_item = db_session.query(QuoteItem).filter_by(name="Offset internal metric").one()
    assert (
        stored_item.internal_cost_snapshot["metrics"]["sheets"]
        == stored_item.total_sheets_with_merma
    )
    assert item["internal_cost_breakdown"]["paper"] != "no indicado"
    assert item["internal_cost_breakdown"]["printing"] == "$0"


def test_plotter_internal_cost_uses_billable_sqm(authorized_client: TestClient, api_seeded_db):
    db_session, seed_data = api_seeded_db
    from quote.repo.models import Paper

    paper = Paper(name="Internal Plotter", weight=1)
    db_session.add(paper)
    db_session.flush()
    db_session.add_all(
        [
            PlotterPricing(
                paper_id=paper.id,
                billing_metric=PlotterBillingMetric.SQM,
                minimum=1,
                maximum=5,
                unit_price=100,
            ),
            PaperInternalCost(
                paper_id=paper.id,
                print_type=PrintType.PLOTTER,
                unit=Unit.SQM,
                paper_cost=4,
                printing_cost=0,
            ),
        ]
    )
    db_session.commit()
    response = authorized_client.post(
        "/api/quotes/",
        json={
            "client_id": seed_data["client_company"].id,
            "items": [
                {
                    "name": "Plotter internal metric",
                    "print_type": "plotter",
                    "quantity": 1,
                    "width_cm": 10,
                    "height_cm": 10,
                    "material_type": "Internal Plotter",
                    "color_mode": "4/0",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text
    item = response.json()["items"][0]
    assert item["square_meters"] == "0.01"
    assert item["internal_cost_breakdown"]["paper"] == "$4"
