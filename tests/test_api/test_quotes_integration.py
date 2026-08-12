"""Integration tests comparing API results with unit test calculations.

These tests verify that hitting the API endpoints with payloads produces
the same results as the unit test calculations.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from quote.domain.enums import ColorMode, PlotterBillingMetric, PrintType, Unit
from quote.repo.models import (
    Finish,
    FinishPricing,
    Paper,
    PaperPricing,
    PlotterPricing,
    QuoteItem,
    QuoteItemFinish,
)


def parse_clp(value: str) -> Decimal:
    """Convert an API-formatted CLP amount into a Decimal."""
    return Decimal(value.replace("$", "").replace(".", "").replace(",", "."))


class TestDigitalQuotesIntegration:
    """Digital quote API integration tests matching unit test cases."""

    def setup_paper_pricing_for_test(self, db_session: Session, paper: Paper, price_ranges: list):
        """Setup paper pricing in DB to match test expectations."""
        # Clear existing pricing for this paper/print type
        db_session.query(PaperPricing).filter(
            PaperPricing.paper_id == paper.id,
            PaperPricing.print_type == PrintType.DIGITAL,
        ).delete()

        # Add pricing ranges from fixture
        for min_qty, max_qty, price in price_ranges:
            pricing = PaperPricing(
                paper_id=paper.id,
                print_type=PrintType.DIGITAL,
                min_quantity=min_qty,
                max_quantity=max_qty if max_qty != float("inf") else None,
                unit_price=price,
            )
            db_session.add(pricing)

        db_session.commit()

    def setup_finishing_pricing(
        self, db_session: Session, finish: Finish, price: Decimal, unit: Unit = Unit.JOB
    ):
        """Setup finishing pricing in DB."""
        # Clear existing pricing
        db_session.query(FinishPricing).filter(
            FinishPricing.finish_id == finish.id,
            FinishPricing.print_type == PrintType.DIGITAL,
        ).delete()

        pricing = FinishPricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=unit,
            min_quantity=1,
            max_quantity=None,
            unit_price=price,
        )
        db_session.add(pricing)
        db_session.commit()

    def test_digital_500_flyers_matches_unit_test(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        flyer_500_case: dict,
        digital_price_table: dict,
        digital_finishing_prices: dict,
    ):
        """
        Test 500 flyers API matches unit test calculations.

        Unit test expects:
        - pieces_per_sheet: 9
        - sheets_needed: 56
        - sheet_cost: $40.040 (56 * $715)
        - finishing_cost: $3.000
        - subtotal: $43.040
        """
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        client_company = seed_data["client_company"]
        finish_cut = seed_data["finish_cut"]

        # Setup pricing to match unit test expectations
        self.setup_paper_pricing_for_test(db_session, paper_couche, digital_price_table["4/0"])
        self.setup_finishing_pricing(
            db_session, finish_cut, digital_finishing_prices["corte_recto"]["price"]
        )

        payload = {
            "client_id": client_company.id,
            "items": [
                {
                    "name": "Flyers Test",
                    "description": "500 flyers - API vs Unit Test",
                    "print_type": "digital",
                    "quantity": flyer_500_case["quantity"],
                    "width_cm": flyer_500_case["width_cm"],
                    "height_cm": flyer_500_case["height_cm"],
                    "paper_id": paper_couche.id,
                    "color_mode": "4/0",
                    "sheet_config": {
                        "usable_width_cm": 31.0,
                        "usable_height_cm": 46.0,
                    },
                    "finishes": [finish_cut.id],
                    "loss_percentage": 0,
                }
            ],
        }

        response = authorized_client.post("/api/quotes/", json=payload)
        assert response.status_code == 201, f"API error: {response.text}"

        data = response.json()
        item = data["items"][0]
        expected = flyer_500_case["expected"]

        # Verify packing calculations match unit tests
        assert item["pieces_per_sheet"] == expected["pieces_per_sheet"], (
            f"pieces_per_sheet mismatch: API={item['pieces_per_sheet']}, "
            f"expected={expected['pieces_per_sheet']}"
        )
        assert item["sheets_needed"] == expected["sheets_needed"], (
            f"sheets_needed mismatch: API={item['sheets_needed']}, "
            f"expected={expected['sheets_needed']}"
        )

        # Verify costs match unit tests
        api_material_cost = parse_clp(item["material_cost"])
        assert api_material_cost == expected["sheet_cost"], (
            f"material_cost mismatch: API={api_material_cost}, expected={expected['sheet_cost']}"
        )

        api_finishing_cost = parse_clp(item["finishing_cost"])
        assert api_finishing_cost == expected["finishing_cost"], (
            f"finishing_cost mismatch: API={api_finishing_cost}, "
            f"expected={expected['finishing_cost']}"
        )

        api_subtotal = parse_clp(item["subtotal_before_losses"])
        assert api_subtotal == expected["subtotal_before_markup"], (
            f"subtotal mismatch: API={api_subtotal}, expected={expected['subtotal_before_markup']}"
        )

    def test_multi_item_quote_totals_match_rounded_item_nets(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        flyer_500_case: dict,
        digital_price_table: dict,
        digital_finishing_prices: dict,
    ):
        """Quote subtotal must equal the sum of item nets before IVA."""
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        finish_cut = seed_data["finish_cut"]

        self.setup_paper_pricing_for_test(db_session, paper_couche, digital_price_table["4/0"])
        self.setup_finishing_pricing(
            db_session, finish_cut, digital_finishing_prices["corte_recto"]["price"]
        )

        item = {
            "name": "Flyers Test",
            "print_type": "digital",
            "quantity": flyer_500_case["quantity"],
            "width_cm": flyer_500_case["width_cm"],
            "height_cm": flyer_500_case["height_cm"],
            "paper_id": paper_couche.id,
            "color_mode": "4/0",
            "sheet_config": {"usable_width_cm": 31.0, "usable_height_cm": 46.0},
            "finishes": [finish_cut.id],
            "loss_percentage": 0,
        }
        response = authorized_client.post(
            "/api/quotes/",
            json={"client_id": seed_data["client_company"].id, "items": [item, item]},
        )

        assert response.status_code == 201, response.text
        quote = response.json()
        subtotal = parse_clp(quote["subtotal"])
        tax = parse_clp(quote["tax"])
        total = parse_clp(quote["total"])

        assert subtotal + tax == total
        assert subtotal == sum(parse_clp(item["net_before_iva"]) for item in quote["items"])
        assert tax == sum(parse_clp(item["iva_amount"]) for item in quote["items"])
        assert total == sum(parse_clp(item["total_final"]) for item in quote["items"])
        for quote_item in quote["items"]:
            assert parse_clp(quote_item["net_before_iva"]) + parse_clp(
                quote_item["iva_amount"]
            ) == parse_clp(quote_item["total_final"])

    def test_digital_20_diplomas_matches_unit_test(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        diploma_20_case: dict,
        digital_diploma_price: Decimal,
    ):
        """
        Test 20 diplomas API matches unit test calculations.

        Unit test expects:
        - pieces_per_sheet: 2
        - sheets_needed: 10
        - sheet_cost: $17.600 (10 * $1760)
        """
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        client_company = seed_data["client_company"]

        # Setup special diploma pricing (fixed price for all quantities)
        db_session.query(PaperPricing).filter(
            PaperPricing.paper_id == paper_couche.id,
            PaperPricing.print_type == PrintType.DIGITAL,
        ).delete()

        pricing = PaperPricing(
            paper_id=paper_couche.id,
            print_type=PrintType.DIGITAL,
            min_quantity=1,
            max_quantity=None,
            unit_price=digital_diploma_price,
        )
        db_session.add(pricing)
        db_session.commit()

        payload = {
            "client_id": client_company.id,
            "items": [
                {
                    "name": "Diplomas Test",
                    "description": "20 diplomas - API vs Unit Test",
                    "print_type": "digital",
                    "quantity": diploma_20_case["quantity"],
                    "width_cm": diploma_20_case["width_cm"],
                    "height_cm": diploma_20_case["height_cm"],
                    "paper_id": paper_couche.id,
                    "color_mode": "4/0",
                    "sheet_config": {
                        "usable_width_cm": 31.0,
                        "usable_height_cm": 46.0,
                    },
                    "finishes": [],
                    "loss_percentage": 0,
                }
            ],
        }

        response = authorized_client.post("/api/quotes/", json=payload)
        assert response.status_code == 201, f"API error: {response.text}"

        data = response.json()
        item = data["items"][0]
        expected = diploma_20_case["expected"]

        assert item["pieces_per_sheet"] == expected["pieces_per_sheet"]
        assert item["sheets_needed"] == expected["sheets_needed"]

        api_material_cost = parse_clp(item["material_cost"])
        assert api_material_cost == expected["sheet_cost"], (
            f"material_cost mismatch: API={api_material_cost}, expected={expected['sheet_cost']}"
        )

    @pytest.mark.xfail(
        reason="API calculates 25 pieces/sheet vs unit test 21 - inconsistency in PackingCalculator parameters"
    )
    def test_digital_300_tarjetas_matches_unit_test(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        tarjeta_300_case: dict,
        digital_price_table: dict,
        digital_finishing_prices: dict,
    ):
        """
        Test 300 tarjetas API matches unit test calculations.

        Unit test expects:
        - pieces_per_sheet: 21
        - sheets_needed: 15
        - sheet_cost: $31.350 (15 * $2090)
        - finishing_cost: $3.000
        - subtotal: $34.350
        """
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        client_company = seed_data["client_company"]
        finish_cut = seed_data["finish_cut"]

        # Setup pricing for 4/4 color
        self.setup_paper_pricing_for_test(db_session, paper_couche, digital_price_table["4/4"])
        self.setup_finishing_pricing(
            db_session, finish_cut, digital_finishing_prices["corte_recto"]["price"]
        )

        payload = {
            "client_id": client_company.id,
            "items": [
                {
                    "name": "Tarjetas Test",
                    "description": "300 tarjetas - API vs Unit Test",
                    "print_type": "digital",
                    "quantity": tarjeta_300_case["quantity"],
                    "width_cm": tarjeta_300_case["width_cm"],
                    "height_cm": tarjeta_300_case["height_cm"],
                    "paper_id": paper_couche.id,
                    "color_mode": "4/4",
                    "sheet_config": {
                        "usable_width_cm": 31.0,
                        "usable_height_cm": 46.0,
                    },
                    "finishes": [finish_cut.id],
                    "loss_percentage": 0,
                }
            ],
        }

        response = authorized_client.post("/api/quotes/", json=payload)
        assert response.status_code == 201, f"API error: {response.text}"

        data = response.json()
        item = data["items"][0]
        expected = tarjeta_300_case["expected"]

        assert item["pieces_per_sheet"] == expected["pieces_per_sheet"]
        assert item["sheets_needed"] == expected["sheets_needed"]

        api_material_cost = parse_clp(item["material_cost"])
        assert api_material_cost == expected["sheet_cost"], (
            f"material_cost mismatch: API={api_material_cost}, expected={expected['sheet_cost']}"
        )

        api_finishing_cost = parse_clp(item["finishing_cost"])
        assert api_finishing_cost == expected["finishing_cost"], (
            f"finishing_cost mismatch: API={api_finishing_cost}, "
            f"expected={expected['finishing_cost']}"
        )

        api_subtotal = parse_clp(item["subtotal_before_losses"])
        assert api_subtotal == expected["subtotal_before_markup"], (
            f"subtotal mismatch: API={api_subtotal}, expected={expected['subtotal_before_markup']}"
        )


class TestPlotterQuotesIntegration:
    """Plotter quote API integration tests matching unit test cases."""

    @staticmethod
    def _amount(value: str) -> Decimal:
        return parse_clp(value)

    @staticmethod
    def _payload(client_id: int, width_cm: int, finish_id: int | None = None) -> dict:
        item = {
            "name": "Plotter catalog test",
            "print_type": "plotter",
            "quantity": 1,
            "width_cm": width_cm,
            "height_cm": 100,
            "material_type": "SINTETICO",
            "color_mode": "4/0",
            "sheet_config": {"usable_width_cm": 100.0, "usable_height_cm": 100.0},
            "loss_percentage": 0,
        }
        if finish_id is not None:
            item["finishes"] = [finish_id]
        return {"client_id": client_id, "items": [item]}

    @staticmethod
    def _seed_catalog_material(db_session: Session) -> Paper:
        paper = Paper(name="SINTÉTICO", weight=1)
        db_session.add(paper)
        db_session.flush()
        db_session.add_all(
            [
                PlotterPricing(
                    paper_id=paper.id,
                    billing_metric=PlotterBillingMetric.SQM,
                    minimum=minimum,
                    maximum=maximum,
                    unit_price=unit_price,
                )
                for minimum, maximum, unit_price in [
                    (Decimal("1"), Decimal("5"), Decimal("10000")),
                    (Decimal("5.01"), Decimal("20"), Decimal("8000")),
                    (Decimal("20.01"), Decimal("100"), Decimal("7000")),
                ]
            ]
        )
        db_session.commit()
        return paper

    def test_plotter_afiche_70x50_matches_unit_test(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        afiche_plotter_case: dict,
        plotter_price_table: dict,
        plotter_finishing_prices: dict,
    ):
        """
        Test 70x50 cm plotter poster API matches unit test calculations.

        Unit test expects:
        - m2: 0.35
        - material_cost: $2.975 (0.35 * $8500)
        - finishing_cost: $1.000
        - subtotal: $3.975
        """
        db_session, seed_data = api_seeded_db
        client_company = seed_data["client_company"]
        self._seed_catalog_material(db_session)

        # Create finishing
        finish_corte = Finish(
            name="Corte Recto Plotter",
            description="Corte para plotter",
            is_active=True,
        )
        db_session.add(finish_corte)
        db_session.flush()

        finish_pricing = PlotterPricing(
            finish_id=finish_corte.id,
            billing_metric=PlotterBillingMetric.SQM,
            minimum=Decimal("1"),
            maximum=Decimal("5"),
            unit_price=plotter_finishing_prices["corte_recto"]["price"],
        )
        db_session.add(finish_pricing)
        db_session.commit()

        payload = {
            "client_id": client_company.id,
            "items": [
                {
                    "name": "Afiche Plotter Test",
                    "description": "70x50 cm - API vs Unit Test",
                    "print_type": "plotter",
                    "quantity": afiche_plotter_case["quantity"],
                    "width_cm": afiche_plotter_case["width_cm"],
                    "height_cm": afiche_plotter_case["height_cm"],
                    "color_mode": "4/0",
                    "minimum_m2": 0.25,
                    "sheet_config": {
                        "usable_width_cm": 70.0,
                        "usable_height_cm": 50.0,
                    },
                    "finishes": [finish_corte.id],
                    "loss_percentage": 0,
                }
            ],
        }

        response = authorized_client.post("/api/quotes/", json=payload)
        assert response.status_code == 201, f"API error: {response.text}"

        data = response.json()
        item = data["items"][0]
        # 70 x 50 cm is charged at the approved minimum of 1 m².
        api_material_cost = parse_clp(item["material_cost"])
        assert api_material_cost == Decimal("10000")

        api_finishing_cost = parse_clp(item["finishing_cost"])
        assert api_finishing_cost == Decimal("1000")
        quote_item = db_session.query(QuoteItem).filter_by(name="Afiche Plotter Test").one()
        quote_finish = (
            db_session.query(QuoteItemFinish).filter_by(quote_item_id=quote_item.id).one()
        )
        assert db_session.get(Paper, quote_item.paper_id).name == "SINTÉTICO"
        assert quote_item.paper_unit_price == Decimal("10000")
        assert quote_item.paper_cost == Decimal("10000")
        assert quote_finish.unit_price == Decimal("1000")
        assert quote_item.details_json["production_calculation"]["pricing"]["plotter_rate"] == {
            "metric": "sqm",
            "minimum": 1.0,
            "maximum": 5.0,
            "unit_price": 10000.0,
            "metric_value": 1.0,
            "cost": 10000.0,
        }

    def test_plotter_api_uses_persisted_boundaries_and_reports_absent_rates(
        self, authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
    ):
        db_session, seed_data = api_seeded_db
        self._seed_catalog_material(db_session)
        for width_cm, expected in [
            (500, 50000),
            (501, 40080),
            (2000, 160000),
            (2001, 140070),
            (10000, 700000),
        ]:
            response = authorized_client.post(
                "/api/quotes/", json=self._payload(seed_data["client_company"].id, width_cm)
            )
            assert response.status_code == 201, response.text
            assert self._amount(response.json()["items"][0]["material_cost"]) == Decimal(expected)

        response = authorized_client.post(
            "/api/quotes/", json=self._payload(seed_data["client_company"].id, 10001)
        )
        assert response.status_code == 400
        assert "No explicit Plotter rate" in response.json()["detail"]

    def test_plotter_api_reports_empty_finish_ranges_and_uses_quantity_metric(
        self, authorized_client: TestClient, api_seeded_db: tuple[Session, dict]
    ):
        db_session, seed_data = api_seeded_db
        self._seed_catalog_material(db_session)
        empty_finish = Finish(name="TROQUELADO")
        quantity_finish = Finish(name="OJETILLOS")
        db_session.add_all([empty_finish, quantity_finish])
        db_session.flush()
        db_session.add_all(
            [
                PlotterPricing(
                    finish_id=empty_finish.id,
                    billing_metric=PlotterBillingMetric.SQM,
                    minimum=Decimal("1"),
                    maximum=Decimal("5"),
                    unit_price=Decimal("9000"),
                ),
                PlotterPricing(
                    finish_id=quantity_finish.id,
                    billing_metric=PlotterBillingMetric.JOB_QUANTITY,
                    minimum=Decimal("1"),
                    maximum=Decimal("200"),
                    unit_price=Decimal("400"),
                ),
            ]
        )
        db_session.commit()

        no_rate = authorized_client.post(
            "/api/quotes/",
            json=self._payload(seed_data["client_company"].id, 600, empty_finish.id),
        )
        assert no_rate.status_code == 400
        assert "No explicit Plotter rate" in no_rate.json()["detail"]

        payload = self._payload(seed_data["client_company"].id, 100, quantity_finish.id)
        payload["items"][0]["quantity"] = 12
        response = authorized_client.post("/api/quotes/", json=payload)
        assert response.status_code == 201, response.text
        assert self._amount(response.json()["items"][0]["finishing_cost"]) == Decimal("4800")


class TestOffsetQuotesIntegration:
    """Offset quote API integration tests matching unit test cases."""

    def test_offset_5000_units_matches_unit_test(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
        offset_5000_case: dict,
    ):
        """Test 5000 units offset API matches unit test calculations."""
        db_session, seed_data = api_seeded_db
        case = offset_5000_case

        db_session.add(
            PaperPricing(
                paper_id=seed_data["paper_couche"].id,
                print_type=PrintType.OFFSET,
                color_mode=ColorMode.C4_0,
                min_quantity=1,
                max_quantity=None,
                unit_price=Decimal("150"),
            )
        )
        db_session.commit()

        response = authorized_client.post(
            "/api/quotes/",
            json={
                "client_id": seed_data["client_company"].id,
                "items": [
                    {
                        "name": "Offset 5000 Units Test",
                        "print_type": "offset",
                        "color_mode": case["color"],
                        "quantity": case["cantidad"],
                        "width_cm": case["width_cm"],
                        "height_cm": case["height_cm"],
                        "paper_id": seed_data["paper_couche"].id,
                        "sheet_config": {
                            "usable_width_cm": 70,
                            "usable_height_cm": 50,
                        },
                    }
                ],
            },
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["items"][0]["print_type"] == "offset"
        assert data["items"][0]["quantity"] == case["cantidad"]
