"""Tests for clients API endpoints."""

from fastapi.testclient import TestClient

from quote.api.deps import get_current_user
from quote.api.main import app
from quote.domain.enums import ClientType, UserRole
from quote.repo.models import Client


class TestCreateClient:
    """Tests for POST /clients/ endpoint."""

    def test_create_individual_client_success(self, authorized_client: TestClient):
        """Test creating a new individual client."""
        client_data = {
            "tax_id": "12.345.678-9",
            "client_type": "individual",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.com",
            "phone": "+56912345678",
            "address": "123 Main St",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        if response.status_code != 201:
            print(f"Response: {response.status_code}")
            print(f"Body: {response.text}")

        assert response.status_code == 201
        data = response.json()
        assert data["tax_id"] == "12.345.678-9"
        assert data["client_type"] == "individual"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@test.com"
        assert "id" in data

    def test_create_company_client_success(self, authorized_client: TestClient):
        """Test creating a new company client."""
        client_data = {
            "tax_id": "76.123.456-7",
            "client_type": "company",
            "company_name": "Test Company S.A.",
            "email": "company@test.com",
            "phone": "+56987654321",
            "address": "456 Business Ave",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 201
        data = response.json()
        assert data["tax_id"] == "76.123.456-7"
        assert data["client_type"] == "company"
        assert data["company_name"] == "Test Company S.A."
        assert data["email"] == "company@test.com"
        assert "id" in data

    def test_create_individual_client_missing_first_name_returns_400(
        self, authorized_client: TestClient
    ):
        """Test creating individual without first_name returns 400."""
        client_data = {
            "tax_id": "12.345.678-9",
            "client_type": "individual",
            "last_name": "Doe",
            "email": "john.doe@test.com",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 400
        assert "first_name" in response.json()["detail"].lower()

    def test_create_individual_client_missing_last_name_returns_400(
        self, authorized_client: TestClient
    ):
        """Test creating individual without last_name returns 400."""
        client_data = {
            "tax_id": "12.345.678-9",
            "client_type": "individual",
            "first_name": "John",
            "email": "john.doe@test.com",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 400
        assert "last_name" in response.json()["detail"].lower()

    def test_create_company_client_missing_company_name_returns_400(
        self, authorized_client: TestClient
    ):
        """Test creating company without company_name returns 400."""
        client_data = {
            "tax_id": "76.123.456-7",
            "client_type": "company",
            "email": "company@test.com",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 400
        assert "company_name" in response.json()["detail"].lower()

    def test_create_client_missing_tax_id_returns_422(self, authorized_client: TestClient):
        """Test creating client without tax_id returns 422."""
        client_data = {
            "client_type": "individual",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 422

    def test_create_client_duplicate_tax_id_returns_400(
        self, authorized_client: TestClient, api_sample_client
    ):
        """Test creating client with duplicate tax_id returns 400."""
        client_data = {
            "tax_id": api_sample_client.tax_id,  # Duplicate
            "client_type": "individual",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
        }
        response = authorized_client.post("/api/clients/", json=client_data)

        assert response.status_code == 400
        assert "detail" in response.json()


class TestListClients:
    """Tests for GET /clients/ endpoint."""

    def test_list_clients_success(self, authorized_client: TestClient, api_sample_client):
        """Test listing all clients."""
        response = authorized_client.get("/api/clients/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(client["tax_id"] == api_sample_client.tax_id for client in data)


class TestGetClient:
    """Tests for GET /clients/{client_id} endpoint."""

    def test_get_client_by_id_success(self, authorized_client: TestClient, api_sample_client):
        """Test getting client by ID."""
        response = authorized_client.get(f"/api/clients/{api_sample_client.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == api_sample_client.id
        assert data["tax_id"] == api_sample_client.tax_id

    def test_get_client_not_found_returns_404(self, authorized_client: TestClient):
        """Test getting non-existent client returns 404."""
        response = authorized_client.get("/api/clients/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Client not found"


class TestUpdateClient:
    """Tests for PATCH /clients/{client_id} endpoint."""

    def test_update_client_email_success(self, authorized_client: TestClient, api_sample_client):
        """Test updating client email."""
        update_data = {"email": "updated@test.com"}
        response = authorized_client.patch(f"/api/clients/{api_sample_client.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@test.com"
        assert data["tax_id"] == api_sample_client.tax_id  # Unchanged

    def test_update_client_phone_success(self, authorized_client: TestClient, api_sample_client):
        """Test updating client phone."""
        update_data = {"phone": "+56999999999"}
        response = authorized_client.patch(f"/api/clients/{api_sample_client.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+56999999999"

    def test_update_client_address_success(self, authorized_client: TestClient, api_sample_client):
        """Test updating client address."""
        update_data = {"address": "New Address 123"}
        response = authorized_client.patch(f"/api/clients/{api_sample_client.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "New Address 123"

    def test_update_individual_client_names_success(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test updating individual client names."""
        from quote.repo.sql_repo import SQLClientRepository

        client_repo = SQLClientRepository(api_test_state.session)
        individual = client_repo.create_individual(
            tax_id="98.765.432-1",
            first_name="Original",
            last_name="Name",
            email="original@test.com",
        )
        api_test_state.session.commit()

        update_data = {"first_name": "Updated", "last_name": "Surname"}
        response = authorized_client.patch(f"/api/clients/{individual.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Surname"

    def test_update_company_client_name_success(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test updating company client name."""
        from quote.repo.sql_repo import SQLClientRepository

        client_repo = SQLClientRepository(api_test_state.session)
        company = client_repo.create_company(
            tax_id="99.888.777-6",
            company_name="Original Company",
            email="company@test.com",
        )

        update_data = {"company_name": "Updated Company S.A."}
        response = authorized_client.patch(f"/api/clients/{company.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Company S.A."

    def test_update_client_not_found_returns_404(self, authorized_client: TestClient):
        """Test updating non-existent client returns 404."""
        update_data = {"email": "updated@test.com"}
        response = authorized_client.patch("/api/clients/99999", json=update_data)

        assert response.status_code == 404
        assert response.json()["detail"] == "Client not found"


class TestDeleteClient:
    """Tests for DELETE /clients/{client_id} endpoint."""

    def test_delete_client_success(self, authorized_client: TestClient, api_test_state):
        """Test soft deleting a client."""
        import uuid

        from quote.repo.sql_repo import SQLClientRepository

        # Create a client to delete with unique tax_id
        client_repo = SQLClientRepository(api_test_state.session)
        unique_tax_id = f"{uuid.uuid4().hex[:8]}.123.456-7"
        client = client_repo.create_individual(
            tax_id=unique_tax_id,
            first_name="To",
            last_name="Delete",
            email=f"delete_{uuid.uuid4().hex[:8]}@test.com",
        )

        response = authorized_client.delete(f"/api/clients/{client.id}")

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_client_not_found_returns_404(self, authorized_client: TestClient):
        """Test deleting non-existent client returns 404."""
        response = authorized_client.delete("/api/clients/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Client not found"

    def test_delete_already_deleted_client_returns_404(
        self, authorized_client: TestClient, api_test_state
    ):
        """Test deleting already deleted client returns 404."""
        import uuid

        from quote.repo.sql_repo import SQLClientRepository

        # Create and delete a client
        client_repo = SQLClientRepository(api_test_state.session)
        unique_tax_id = f"{uuid.uuid4().hex[:8]}.222.333-4"
        client = client_repo.create_individual(
            tax_id=unique_tax_id,
            first_name="Already",
            last_name="Deleted",
            email=f"alreadydeleted_{uuid.uuid4().hex[:8]}@test.com",
        )
        assert client.id is not None
        api_test_state.session.commit()
        client_repo.soft_delete(client.id)
        api_test_state.session.commit()

        # Try to delete again
        response = authorized_client.delete(f"/api/clients/{client.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Client not found or already deleted"


def test_seller_cannot_access_another_seller_client(api_client, api_test_state, api_user_factory):
    """Ownership limits non-admin profiles to clients they created."""
    owner = api_user_factory(name="Owner", email="owner@test.com", role=UserRole.VENDEDOR)
    other = api_user_factory(name="Other", email="other@test.com", role=UserRole.VENDEDOR)
    client = Client(
        client_type=ClientType.COMPANY,
        tax_id="76.000.000-1",
        company_name="Private client",
        created_by_id=owner.id,
    )
    api_test_state.session.add(client)
    api_test_state.session.commit()
    app.dependency_overrides[get_current_user] = lambda: other

    assert api_client.get(f"/api/clients/{client.id}").status_code == 403
    assert api_client.get("/api/clients/").json() == []
