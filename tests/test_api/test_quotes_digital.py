"""Tests for digital quote API endpoints - Bug fix verification."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestDigitalQuotePaperPriceBug:
    """
    Test to verify paper price is calculated based on sheets_needed, not quantity.

    Bug: When calculating a quote for 500 flyers with 9 pieces per sheet,
    we need 56 sheets. The paper price should be looked up using 56 sheets
    (price $715 for range 1-100), NOT using quantity 500 (price $650 for range 101-500).
    """

    def test_digital_quote_uses_sheets_not_quantity_for_paper_price(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
    ):
        """
        Verify that paper price lookup uses sheets_needed, not item quantity.

        Scenario:
        - 500 flyers
        - 9 pieces per sheet (packing calculation)
        - 56 sheets needed (ceil(500/9))
        - Paper price should be $715 (range 1-100 sheets), NOT $650 (range 101-500 quantity)
        """
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        client_company = seed_data["client_company"]
        finish_cut = seed_data["finish_cut"]

        # Request payload for 500 flyers
        payload = {
            "client_id": client_company.id,
            "items": [
                {
                    "name": "Flyers Corporativos",
                    "description": "500 flyers para evento",
                    "print_type": "digital",
                    "quantity": 500,
                    "width_cm": 10.0,
                    "height_cm": 15.0,
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

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )

        data = response.json()
        item = data["items"][0]

        # Verify sheets calculation
        assert item["pieces_per_sheet"] == 9, (
            f"Expected 9 pieces per sheet, got {item['pieces_per_sheet']}"
        )
        assert item["sheets_needed"] == 56, f"Expected 56 sheets, got {item['sheets_needed']}"

        # CRITICAL: Verify paper price uses sheets (56), NOT quantity (500)
        # With 56 sheets, should get price $715 (range 1-100)
        # BUG: With 500 quantity, would get price $650 (range 101-500)
        expected_paper_price = Decimal("715")
        # Parse formatted CLP price (e.g., "$715,00" -> 715.00)
        paper_price_str = (
            str(item["paper_unit_price"]).replace("$", "").replace(".", "").replace(",", ".")
        )
        actual_paper_price = Decimal(paper_price_str)

        assert actual_paper_price == expected_paper_price, (
            f"Paper price should be {expected_paper_price} (based on 56 sheets, range 1-100), "
            f"but got {actual_paper_price}. "
            f"This indicates the price lookup is using quantity (500) instead of sheets_needed (56)."
        )

        # Verify material cost calculation
        expected_material_cost = Decimal("40040")  # 56 sheets * $715
        actual_material_cost = Decimal(
            str(item["material_cost"]).replace("$", "").replace(".", "").replace(",", ".")
        )

        assert actual_material_cost == expected_material_cost, (
            f"Material cost should be {expected_material_cost} (56 sheets * $715), "
            f"but got {actual_material_cost}"
        )

    def test_digital_quote_multiple_quantity_ranges(
        self,
        authorized_client: TestClient,
        api_seeded_db: tuple[Session, dict],
    ):
        """
        Test multiple quantities to ensure paper price always uses sheets.

        Test cases:
        - 500 flyers → 56 sheets → price $715 (range 1-100)
        - 1000 flyers → 112 sheets → price $650 (range 101-500 sheets)
        """
        db_session, seed_data = api_seeded_db
        paper_couche = seed_data["paper_couche"]
        client_company = seed_data["client_company"]

        test_cases = [
            # (quantity, expected_sheets, expected_price, description)
            (500, 56, Decimal("715"), "500 flyers → 56 sheets → range 1-100"),
            (900, 100, Decimal("715"), "900 flyers → 100 sheets → range 1-100"),
            (1000, 112, Decimal("650"), "1000 flyers → 112 sheets → range 101-500"),
        ]

        for quantity, expected_sheets, expected_price, description in test_cases:
            payload = {
                "client_id": client_company.id,
                "items": [
                    {
                        "name": f"Test {quantity} units",
                        "print_type": "digital",
                        "quantity": quantity,
                        "width_cm": 10.0,
                        "height_cm": 15.0,
                        "paper_id": paper_couche.id,
                        "color_mode": "4/4",
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

            assert response.status_code == 201, f"Failed for {description}: {response.text}"

            data = response.json()
            item = data["items"][0]

            actual_sheets = item["sheets_needed"]
            # Parse formatted CLP price
            price_str = (
                str(item["paper_unit_price"]).replace("$", "").replace(".", "").replace(",", ".")
            )
            actual_price = Decimal(price_str)

            assert actual_sheets == expected_sheets, (
                f"{description}: Expected {expected_sheets} sheets, got {actual_sheets}"
            )

            assert actual_price == expected_price, (
                f"{description}: Expected price {expected_price}, got {actual_price}"
            )
