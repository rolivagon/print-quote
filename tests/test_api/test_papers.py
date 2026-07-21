"""Tests for papers API endpoints."""

from fastapi.testclient import TestClient


class TestCreatePaper:
    """Tests for POST /papers/ endpoint."""

    def test_create_paper_success(self, authorized_client: TestClient):
        """Test creating a new paper."""
        paper_data = {
            "name": "Test Paper 200g",
            "weight": 200,
            "description": "A test paper for printing",
            "is_active": True,
        }
        response = authorized_client.post("/api/papers/", json=paper_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Paper 200g"
        assert data["weight"] == 200
        assert data["description"] == "A test paper for printing"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_paper_minimal_data(self, authorized_client: TestClient):
        """Test creating a paper with minimal data."""
        paper_data = {
            "name": "Minimal Paper",
            "weight": 100,
        }
        response = authorized_client.post("/api/papers/", json=paper_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Paper"
        assert data["weight"] == 100
        assert data["is_active"] is True  # Default value

    def test_create_paper_missing_name_returns_422(self, authorized_client: TestClient):
        """Test creating paper without name returns 422."""
        paper_data = {"weight": 100}
        response = authorized_client.post("/api/papers/", json=paper_data)

        assert response.status_code == 422

    def test_create_paper_missing_weight_returns_422(self, authorized_client: TestClient):
        """Test creating paper without weight returns 422."""
        paper_data = {"name": "Test Paper"}
        response = authorized_client.post("/api/papers/", json=paper_data)

        assert response.status_code == 422

    def test_create_paper_duplicate_name_returns_400(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test creating paper with duplicate name returns 400."""
        paper_data = {
            "name": api_sample_paper.name,  # Duplicate
            "weight": 150,
        }
        response = authorized_client.post("/api/papers/", json=paper_data)

        assert response.status_code == 400
        assert "detail" in response.json()


class TestListPapers:
    """Tests for GET /papers/ endpoint."""

    def test_list_papers_success(self, authorized_client: TestClient, api_sample_paper):
        """Test listing all papers."""
        response = authorized_client.get("/api/papers/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(paper["name"] == api_sample_paper.name for paper in data)


class TestGetPaper:
    """Tests for GET /papers/{paper_id} endpoint."""

    def test_get_paper_by_id_success(self, authorized_client: TestClient, api_sample_paper):
        """Test getting paper by ID."""
        response = authorized_client.get(f"/api/papers/{api_sample_paper.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == api_sample_paper.id
        assert data["name"] == api_sample_paper.name

    def test_get_paper_not_found_returns_404(self, authorized_client: TestClient):
        """Test getting non-existent paper returns 404."""
        response = authorized_client.get("/api/papers/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found"


class TestUpdatePaper:
    """Tests for PATCH /papers/{paper_id} endpoint."""

    def test_update_paper_name_success(self, authorized_client: TestClient, api_sample_paper):
        """Test updating paper name."""
        update_data = {"name": "Updated Paper Name"}
        response = authorized_client.patch(f"/api/papers/{api_sample_paper.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Paper Name"
        assert data["weight"] == api_sample_paper.weight  # Unchanged

    def test_update_paper_weight_success(self, authorized_client: TestClient, api_sample_paper):
        """Test updating paper weight."""
        update_data = {"weight": 250}
        response = authorized_client.patch(f"/api/papers/{api_sample_paper.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 250

    def test_update_paper_description_success(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test updating paper description."""
        update_data = {"description": "Updated description"}
        response = authorized_client.patch(f"/api/papers/{api_sample_paper.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_paper_is_active_success(self, authorized_client: TestClient, api_sample_paper):
        """Test updating paper is_active status."""
        update_data = {"is_active": False}
        response = authorized_client.patch(f"/api/papers/{api_sample_paper.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_paper_multiple_fields_success(
        self, authorized_client: TestClient, api_sample_paper
    ):
        """Test updating multiple paper fields."""
        update_data = {
            "name": "Multi Update",
            "weight": 300,
            "description": "Multi description",
        }
        response = authorized_client.patch(f"/api/papers/{api_sample_paper.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Multi Update"
        assert data["weight"] == 300
        assert data["description"] == "Multi description"

    def test_update_paper_not_found_returns_404(self, authorized_client: TestClient):
        """Test updating non-existent paper returns 404."""
        update_data = {"name": "Updated Name"}
        response = authorized_client.patch("/api/papers/99999", json=update_data)

        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found"


class TestDeletePaper:
    """Tests for DELETE /papers/{paper_id} endpoint."""

    def test_delete_paper_success(self, authorized_client: TestClient, api_test_state):
        """Test deleting an existing paper."""
        from quote.repo.sql_repo import SQLPaperRepository

        # Create a paper to delete
        paper_repo = SQLPaperRepository(api_test_state.session)
        paper = paper_repo.create(
            name="Paper To Delete",
            weight=150,
        )
        api_test_state.session.commit()

        response = authorized_client.delete(f"/api/papers/{paper.id}")

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_paper_not_found_returns_404(self, authorized_client: TestClient):
        """Test deleting non-existent paper returns 404."""
        response = authorized_client.delete("/api/papers/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found or already deleted"

    def test_delete_already_deleted_paper_returns_404(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test deleting already deleted paper returns 404."""
        from quote.repo.sql_repo import SQLPaperRepository

        # Create and delete a paper
        paper_repo = SQLPaperRepository(api_test_state.session)
        paper = paper_repo.create(
            name="Already Deleted",
            weight=150,
        )
        assert paper.id is not None
        api_test_state.session.commit()
        paper_repo.soft_delete(paper.id)
        api_test_state.session.commit()

        # Try to delete again
        response = authorized_client.delete(f"/api/papers/{paper.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Paper not found or already deleted"
