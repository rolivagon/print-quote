"""Authorization helper tests."""

import pytest

from quote.api.deps import is_admin_role
from quote.domain.enums import UserRole


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.SUPER_ADMIN])
def test_administrative_roles_include_admin_and_super_admin(role):
    """All administrative profiles must receive the same route-level access."""
    assert is_admin_role(role)


def test_vendedor_is_not_an_administrative_role():
    """Seller profiles must not receive administrative access."""
    assert not is_admin_role(UserRole.VENDEDOR)
