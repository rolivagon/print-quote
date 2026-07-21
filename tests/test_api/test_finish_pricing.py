"""Tests for finish pricing API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient


class TestListFinishPricing:
    """Tests for GET /finishes/{finish_id}/pricing endpoint."""

    def test_list_finish_pricing_success(self, authorized_client: TestClient, api_test_state):
        """Test listing all pricing for a finish."""
        from quote.domain.enums import PrintType, Unit
        from quote.repo.models import Finish, FinishPricing

        # Create a finish with pricing
        finish = Finish(
            name="Test Finish for Pricing",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.flush()

        pricing = FinishPricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("5000"),
        )
        api_test_state.session.add(pricing)
        api_test_state.session.commit()

        response = authorized_client.get(f"/api/finishes/{finish.id}/pricing")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all("id" in item for item in data)
        assert all("unit_price" in item for item in data)

    def test_list_finish_pricing_finish_not_found(self, authorized_client: TestClient):
        """Test listing pricing for non-existent finish returns 404."""
        response = authorized_client.get("/api/finishes/99999/pricing")

        assert response.status_code == 404
        assert "detail" in response.json()


class TestCreateFinishPricing:
    """Tests for POST /finishes/{finish_id}/pricing endpoint."""

    def test_create_finish_pricing_success(self, authorized_client: TestClient, api_test_state):
        """Test creating a new pricing entry for a finish."""
        from quote.repo.models import Finish

        finish = Finish(
            name="New Finish",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.commit()
        api_test_state.session.refresh(finish)

        pricing_data = {
            "print_type": "digital",
            "unit": "sheet",
            "min_quantity": 1,
            "max_quantity": 500,
            "unit_price": "150.50",
        }
        response = authorized_client.post(f"/api/finishes/{finish.id}/pricing", json=pricing_data)

        assert response.status_code == 201
        data = response.json()
        assert data["min_quantity"] == 1
        assert data["max_quantity"] == 500
        assert Decimal(data["unit_price"]) == Decimal("150.50")
        assert "id" in data
        assert data["finish_id"] == finish.id

    def test_create_finish_pricing_without_max_quantity(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test creating pricing without max_quantity (open-ended range)."""
        from quote.repo.models import Finish

        finish = Finish(
            name="Finish Open Range",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.commit()
        api_test_state.session.refresh(finish)

        pricing_data = {
            "print_type": "plotter",
            "unit": "sqm",
            "min_quantity": 1000,
            "max_quantity": None,
            "unit_price": "99.99",
        }
        response = authorized_client.post(f"/api/finishes/{finish.id}/pricing", json=pricing_data)

        assert response.status_code == 201
        data = response.json()
        assert data["min_quantity"] == 1000
        assert data["max_quantity"] is None

    def test_create_finish_pricing_finish_not_found(self, authorized_client: TestClient):
        """Test creating pricing for non-existent finish returns 404."""
        pricing_data = {
            "print_type": "digital",
            "unit": "job",
            "min_quantity": 1,
            "max_quantity": 100,
            "unit_price": "50.00",
        }
        response = authorized_client.post("/api/finishes/99999/pricing", json=pricing_data)

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_finish_pricing_invalid_min_quantity(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test creating pricing with invalid min_quantity returns 422."""
        from quote.repo.models import Finish

        finish = Finish(
            name="Finish Invalid Qty",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.commit()
        api_test_state.session.refresh(finish)

        pricing_data = {
            "print_type": "digital",
            "unit": "job",
            "min_quantity": 0,
            "max_quantity": 100,
            "unit_price": "50.00",
        }
        response = authorized_client.post(f"/api/finishes/{finish.id}/pricing", json=pricing_data)

        assert response.status_code == 422


class TestUpdateFinishPricing:
    """Tests for PATCH /finishes/pricing/{pricing_id} endpoint."""

    def test_update_finish_pricing_success(self, authorized_client: TestClient, api_test_state):
        """Test updating a finish pricing entry."""
        from quote.domain.enums import PrintType, Unit
        from quote.repo.models import Finish, FinishPricing

        finish = Finish(
            name="Finish to Update",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.flush()

        pricing = FinishPricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("100.00"),
        )
        api_test_state.session.add(pricing)
        api_test_state.session.commit()
        api_test_state.session.refresh(pricing)

        update_data = {"unit_price": "999.99", "max_quantity": 200}
        response = authorized_client.patch(f"/api/finishes/pricing/{pricing.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["unit_price"]) == Decimal("999.99")
        assert data["max_quantity"] == 200

    def test_update_finish_pricing_not_found(self, authorized_client: TestClient):
        """Test updating non-existent pricing returns 404."""
        update_data = {"unit_price": "999.99"}
        response = authorized_client.patch("/api/finishes/pricing/99999", json=update_data)

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_update_finish_pricing_partial_fields(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test updating only some fields of pricing."""
        from quote.domain.enums import PrintType, Unit
        from quote.repo.models import Finish, FinishPricing

        finish = Finish(
            name="Finish Partial Update",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.flush()

        pricing = FinishPricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=50,
            max_quantity=500,
            unit_price=Decimal("75.00"),
        )
        api_test_state.session.add(pricing)
        api_test_state.session.commit()
        api_test_state.session.refresh(pricing)
        original_min_qty = pricing.min_quantity

        update_data = {"unit_price": "777.77"}
        response = authorized_client.patch(f"/api/finishes/pricing/{pricing.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["unit_price"]) == Decimal("777.77")
        assert data["min_quantity"] == original_min_qty  # Unchanged


class TestDeleteFinishPricing:
    """Tests for DELETE /finishes/pricing/{pricing_id} endpoint."""

    def test_delete_finish_pricing_success(self, authorized_client: TestClient, api_test_state):
        """Test deleting a finish pricing entry."""
        from quote.domain.enums import PrintType, Unit
        from quote.repo.models import Finish, FinishPricing

        finish = Finish(
            name="Finish to Delete Pricing",
            is_active=True,
        )
        api_test_state.session.add(finish)
        api_test_state.session.flush()

        pricing = FinishPricing(
            finish_id=finish.id,
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=1,
            max_quantity=50,
            unit_price=Decimal("25.00"),
        )
        api_test_state.session.add(pricing)
        api_test_state.session.commit()
        api_test_state.session.refresh(pricing)

        response = authorized_client.delete(f"/api/finishes/pricing/{pricing.id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify it's deleted
        deleted_pricing = (
            api_test_state.session.query(FinishPricing).filter_by(id=pricing.id).first()
        )
        assert deleted_pricing is None

    def test_delete_finish_pricing_not_found(self, authorized_client: TestClient):
        """Test deleting non-existent pricing returns 404."""
        # Use a high ID that doesn't exist
        response = authorized_client.delete("/api/finishes/pricing/99999")

        assert response.status_code == 404
        assert "detail" in response.json()
