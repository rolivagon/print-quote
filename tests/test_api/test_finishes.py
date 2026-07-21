"""Tests for finishes API endpoints."""

from fastapi.testclient import TestClient


class TestCreateFinish:
    """Tests for POST /finishes/ endpoint."""

    def test_create_finish_success(self, authorized_client: TestClient):
        """Test creating a new finish."""
        finish_data = {
            "name": "Laminado Mate",
            "description": "Laminado mate",
            "is_active": True,
        }
        response = authorized_client.post("/api/finishes/", json=finish_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Laminado Mate"
        assert data["description"] == "Laminado mate"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_finish_minimal_data(self, authorized_client: TestClient):
        """Test creating a finish with minimal data."""
        finish_data = {
            "name": "Corte Simple",
        }
        response = authorized_client.post("/api/finishes/", json=finish_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Corte Simple"
        assert data["is_active"] is True  # Default value

    def test_create_finish_missing_name_returns_422(self, authorized_client: TestClient):
        """Test creating finish without name returns 422."""
        finish_data = {}
        response = authorized_client.post("/api/finishes/", json=finish_data)

        assert response.status_code == 422

    def test_create_finish_duplicate_name_returns_400(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test creating finish with duplicate name returns 400."""
        from quote.repo.sql_repo import SQLFinishRepository

        # Create first finish
        finish_repo = SQLFinishRepository(api_test_state.session)
        finish_repo.create(
            name="Duplicate Finish",
        )

        # Try to create duplicate
        finish_data = {
            "name": "Duplicate Finish",
        }
        response = authorized_client.post("/api/finishes/", json=finish_data)

        assert response.status_code == 400
        assert "detail" in response.json()


class TestListFinishes:
    """Tests for GET /finishes/ endpoint."""

    def test_list_finishes_success(self, authorized_client: TestClient, api_test_state):
        """Test listing all finishes."""
        from quote.repo.sql_repo import SQLFinishRepository

        # Create a finish first
        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="List Test Finish",
        )

        response = authorized_client.get("/api/finishes/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(f["name"] == finish.name for f in data)


class TestGetFinish:
    """Tests for GET /finishes/{finish_id} endpoint."""

    def test_get_finish_by_id_success(self, authorized_client: TestClient, api_test_state):
        """Test getting finish by ID."""
        from quote.repo.sql_repo import SQLFinishRepository

        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Get Test Finish",
        )

        response = authorized_client.get(f"/api/finishes/{finish.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == finish.id
        assert data["name"] == finish.name

    def test_get_finish_not_found_returns_404(self, authorized_client: TestClient):
        """Test getting non-existent finish returns 404."""
        response = authorized_client.get("/api/finishes/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Finish not found"


class TestUpdateFinish:
    """Tests for PATCH /finishes/{finish_id} endpoint."""

    def test_update_finish_name_success(self, authorized_client: TestClient, api_test_state):
        """Test updating finish name."""
        from quote.repo.sql_repo import SQLFinishRepository

        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Original Finish",
        )

        update_data = {"name": "Updated Finish Name"}
        response = authorized_client.patch(f"/api/finishes/{finish.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Finish Name"

    def test_update_finish_description_success(self, authorized_client: TestClient, api_test_state):
        """Test updating finish description."""
        from quote.repo.sql_repo import SQLFinishRepository

        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Desc Test Finish",
            description="Original description",
        )

        update_data = {"description": "Updated description"}
        response = authorized_client.patch(f"/api/finishes/{finish.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_finish_is_active_success(self, authorized_client: TestClient, api_test_state):
        """Test updating finish is_active status."""
        from quote.repo.sql_repo import SQLFinishRepository

        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Active Test Finish",
        )

        update_data = {"is_active": False}
        response = authorized_client.patch(f"/api/finishes/{finish.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_finish_not_found_returns_404(self, authorized_client: TestClient):
        """Test updating non-existent finish returns 404."""
        update_data = {"name": "Updated Name"}
        response = authorized_client.patch("/api/finishes/99999", json=update_data)

        assert response.status_code == 404
        assert response.json()["detail"] == "Finish not found"


class TestDeleteFinish:
    """Tests for DELETE /finishes/{finish_id} endpoint."""

    def test_delete_finish_success(self, authorized_client: TestClient, api_test_state):
        """Test soft deleting a finish."""
        from quote.repo.sql_repo import SQLFinishRepository

        # Create a finish to delete
        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Finish To Delete",
        )

        response = authorized_client.delete(f"/api/finishes/{finish.id}")

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_finish_not_found_returns_404(self, authorized_client: TestClient):
        """Test deleting non-existent finish returns 404."""
        response = authorized_client.delete("/api/finishes/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Finish not found or already deleted"

    def test_delete_already_deleted_finish_returns_404(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test deleting already deleted finish returns 404."""
        from quote.repo.sql_repo import SQLFinishRepository

        # Create and delete a finish
        finish_repo = SQLFinishRepository(api_test_state.session)
        finish = finish_repo.create(
            name="Already Deleted",
        )
        assert finish.id is not None
        finish_repo.soft_delete(finish.id)

        # Try to delete again
        response = authorized_client.delete(f"/api/finishes/{finish.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Finish not found or already deleted"
