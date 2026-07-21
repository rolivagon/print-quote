"""Tests for paper pricing API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient


class TestListPaperPricing:
    """Tests for GET /papers/{paper_id}/pricing endpoint."""

    def test_list_paper_pricing_success(self, authorized_client: TestClient, api_sample_paper):
        """Test listing all pricing for a paper."""
        response = authorized_client.get(f"/api/papers/{api_sample_paper.id}/pricing")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all("id" in item for item in data)
        assert all("print_type" in item for item in data)
        assert all("unit_price" in item for item in data)

    def test_list_paper_pricing_paper_not_found(self, authorized_client: TestClient):
        """Test listing pricing for non-existent paper returns 404."""
        response = authorized_client.get("/api/papers/99999/pricing")

        assert response.status_code == 404
        assert "detail" in response.json()


class TestCreatePaperPricing:
    """Tests for POST /papers/{paper_id}/pricing endpoint."""

    def test_create_paper_pricing_success(self, authorized_client: TestClient, api_sample_paper):
        """Test creating a new pricing entry for a paper."""
        pricing_data = {
            "print_type": "offset",
            "min_quantity": 1,
            "max_quantity": 500,
            "unit_price": "150.50",
        }
        response = authorized_client.post(
            f"/api/papers/{api_sample_paper.id}/pricing", json=pricing_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["print_type"] == "offset"
        assert data["min_quantity"] == 1
        assert data["max_quantity"] == 500
        assert Decimal(data["unit_price"]) == Decimal("150.50")
        assert "id" in data
        assert data["paper_id"] == api_sample_paper.id

    def test_create_paper_pricing_without_max_quantity(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test creating pricing without max_quantity (open-ended range)."""
        pricing_data = {
            "print_type": "plotter",
            "min_quantity": 1000,
            "max_quantity": None,
            "unit_price": "99.99",
        }
        response = authorized_client.post(
            f"/api/papers/{api_sample_paper.id}/pricing", json=pricing_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["min_quantity"] == 1000
        assert data["max_quantity"] is None

    def test_create_paper_pricing_paper_not_found(self, authorized_client: TestClient):
        """Test creating pricing for non-existent paper returns 404."""
        pricing_data = {
            "print_type": "digital",
            "min_quantity": 1,
            "max_quantity": 100,
            "unit_price": "50.00",
        }
        response = authorized_client.post("/api/papers/99999/pricing", json=pricing_data)

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_paper_pricing_invalid_min_quantity(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test creating pricing with invalid min_quantity returns 422."""
        pricing_data = {
            "print_type": "digital",
            "min_quantity": 0,
            "max_quantity": 100,
            "unit_price": "50.00",
        }
        response = authorized_client.post(
            f"/api/papers/{api_sample_paper.id}/pricing", json=pricing_data
        )

        assert response.status_code == 422

    def test_create_paper_pricing_invalid_print_type(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test creating pricing with invalid print_type returns 422."""
        pricing_data = {
            "print_type": "INVALID",
            "min_quantity": 1,
            "max_quantity": 100,
            "unit_price": "50.00",
        }
        response = authorized_client.post(
            f"/api/papers/{api_sample_paper.id}/pricing", json=pricing_data
        )

        assert response.status_code == 422


class TestUpdatePaperPricing:
    """Tests for PATCH /papers/pricing/{pricing_id} endpoint."""

    def test_update_paper_pricing_success(
        self, authorized_client: TestClient, api_sample_paper, api_test_state
    ):
        """Test updating a paper pricing entry."""
        # Get existing pricing
        from quote.repo.models import PaperPricing

        pricing = (
            api_test_state.session.query(PaperPricing)
            .filter_by(paper_id=api_sample_paper.id)
            .first()
        )
        assert pricing is not None

        update_data = {"unit_price": "999.99", "max_quantity": 200}
        response = authorized_client.patch(f"/api/papers/pricing/{pricing.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["unit_price"]) == Decimal("999.99")
        assert data["max_quantity"] == 200

    def test_update_paper_pricing_not_found(self, authorized_client: TestClient):
        """Test updating non-existent pricing returns 404."""
        update_data = {"unit_price": "999.99"}
        response = authorized_client.patch("/api/papers/pricing/99999", json=update_data)

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_update_paper_pricing_partial_fields(
        self, authorized_client: TestClient, api_sample_paper, api_test_state
    ):
        """Test updating only some fields of pricing."""
        from quote.repo.models import PaperPricing

        pricing = (
            api_test_state.session.query(PaperPricing)
            .filter_by(paper_id=api_sample_paper.id)
            .first()
        )
        original_min_qty = pricing.min_quantity

        update_data = {"unit_price": "777.77"}
        response = authorized_client.patch(f"/api/papers/pricing/{pricing.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["unit_price"]) == Decimal("777.77")
        assert data["min_quantity"] == original_min_qty  # Unchanged


class TestDeletePaperPricing:
    """Tests for DELETE /papers/pricing/{pricing_id} endpoint."""

    def test_delete_paper_pricing_success(
        self, authorized_client: TestClient, api_sample_paper, api_test_state
    ):
        """Test deleting a paper pricing entry."""
        from quote.domain.enums import PrintType
        from quote.repo.models import PaperPricing

        # Create a pricing to delete
        pricing = PaperPricing(
            paper_id=api_sample_paper.id,
            print_type=PrintType.OFFSET,
            min_quantity=1,
            max_quantity=50,
            unit_price=Decimal("25.00"),
        )
        api_test_state.session.add(pricing)
        api_test_state.session.commit()
        api_test_state.session.refresh(pricing)

        response = authorized_client.delete(f"/api/papers/pricing/{pricing.id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify it's deleted
        deleted_pricing = (
            api_test_state.session.query(PaperPricing).filter_by(id=pricing.id).first()
        )
        assert deleted_pricing is None

    def test_delete_paper_pricing_not_found(self, authorized_client: TestClient):
        """Test deleting non-existent pricing returns 404."""
        response = authorized_client.delete("/api/papers/pricing/99999")

        assert response.status_code == 404
        assert "detail" in response.json()
