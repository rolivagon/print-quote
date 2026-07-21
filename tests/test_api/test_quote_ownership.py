"""Quote ownership authorization tests."""

from quote.api.deps import get_current_user
from quote.api.main import app
from quote.domain.enums import ClientType, UserRole
from quote.repo.models import Client


def test_seller_cannot_quote_another_seller_client(api_client, api_test_state, api_user_factory):
    """Quote creation rejects a client not owned by the authenticated seller."""
    owner = api_user_factory(name="Owner", email="quote-owner@test.com", role=UserRole.VENDEDOR)
    other = api_user_factory(name="Other", email="quote-other@test.com", role=UserRole.VENDEDOR)
    client = Client(
        client_type=ClientType.COMPANY,
        tax_id="76.000.000-2",
        company_name="Private client",
        created_by_id=owner.id,
    )
    api_test_state.session.add(client)
    api_test_state.session.commit()
    app.dependency_overrides[get_current_user] = lambda: other

    response = api_client.post(
        "/api/quotes/",
        json={
            "client_id": client.id,
            "items": [
                {
                    "name": "Unauthorized quote",
                    "print_type": "digital",
                    "color_mode": "4/0",
                    "quantity": 1,
                    "width_cm": 10,
                    "height_cm": 10,
                    "paper_id": 1,
                    "sheet_config": {"usable_width_cm": 30, "usable_height_cm": 45},
                }
            ],
        },
    )

    assert response.status_code == 403
