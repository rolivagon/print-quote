"""Tests for flexible finish pricing."""

from fastapi.testclient import TestClient


class TestFinishFlexibility:
    """Tests for the new flexible finish pricing logic."""

    def test_create_finish_simple(self, authorized_client: TestClient):
        """Test creating a finish without unit or type."""
        finish_data = {
            "name": "Flexible Finish",
            "description": "A finish that can be job or item based",
        }
        response = authorized_client.post("/api/finishes/", json=finish_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Flexible Finish"
        assert "unit" not in data  # Should be removed from entity
        assert "finish_type" not in data  # Should be removed from entity

    def test_add_mixed_pricing_logic(self, authorized_client: TestClient, api_test_state):
        """Test adding different pricing units for different print types."""
        from quote.repo.models import Finish

        # Create finish
        finish = Finish(name="Mixed Logic Finish")
        api_test_state.session.add(finish)
        api_test_state.session.commit()
        api_test_state.session.refresh(finish)

        # 1. Add Digital pricing (Per Item)
        digital_pricing = {
            "print_type": "digital",
            "unit": "per_item",
            "min_quantity": 1,
            "max_quantity": None,
            "unit_price": "50.00",
        }
        resp1 = authorized_client.post(f"/api/finishes/{finish.id}/pricing", json=digital_pricing)
        assert resp1.status_code == 201
        assert resp1.json()["unit"] == "per_item"

        # 2. Add Plotter pricing (Per Job)
        plotter_pricing = {
            "print_type": "plotter",
            "unit": "job",
            "min_quantity": 1,
            "max_quantity": None,
            "unit_price": "5000.00",
        }
        resp2 = authorized_client.post(f"/api/finishes/{finish.id}/pricing", json=plotter_pricing)
        assert resp2.status_code == 201
        assert resp2.json()["unit"] == "job"

        # 3. List and verify
        list_resp = authorized_client.get(f"/api/finishes/{finish.id}/pricing")
        data = list_resp.json()
        assert len(data) == 2

        digital_entry = next(item for item in data if item["print_type"] == "digital")
        plotter_entry = next(item for item in data if item["print_type"] == "plotter")

        assert digital_entry["unit"] == "per_item"
        assert plotter_entry["unit"] == "job"
