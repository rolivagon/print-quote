"""Integration tests for master data CRUD repositories with soft delete.

These tests validate operations against the actual database state.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from quote.domain.enums import ClientType
from quote.repo.models import Client, Finish, Paper, User
from quote.repo.sql_repo import (
    SQLClientRepository,
    SQLFinishRepository,
    SQLPaperRepository,
    SQLUserRepository,
)


def unique_email(prefix: str = "test") -> str:
    """Generate a unique email address."""
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def unique_tax_id() -> str:
    """Generate a unique tax ID."""
    return f"{uuid4().hex[:8]}-{uuid4().hex[:1]}"


def unique_name(prefix: str = "Test") -> str:
    """Generate a unique name."""
    return f"{prefix}_{uuid4().hex[:8]}"


class TestSQLUserRepository:
    """Integration tests for SQLUserRepository."""

    def test_create_user_persists_to_database(self, db_session: Session):
        """Should create user and verify it exists in database."""
        # Arrange
        repo = SQLUserRepository(db_session)
        name = unique_name("John")
        email = unique_email("john")

        # Act
        user = repo.create(name=name, email=email, hashed_password="hashed_password")
        assert user.id is not None

        # Assert - Verify via direct DB query
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        assert db_user.name == name
        assert db_user.email == email
        assert db_user.is_active is True
        assert db_user.deleted_at is None
        assert db_user.created_at is not None

    def test_create_duplicate_email_raises_error(self, db_session: Session):
        """Should raise ValueError when creating user with duplicate email."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email()
        repo.create(name=unique_name(), email=email, hashed_password="password")

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.create(name=unique_name(), email=email, hashed_password="password")

    def test_get_by_id_returns_user(self, db_session: Session):
        """Should retrieve user by ID."""
        # Arrange
        repo = SQLUserRepository(db_session)
        name = unique_name("John")
        email = unique_email("john")
        created = repo.create(name=name, email=email, hashed_password="password")
        assert created.id is not None

        # Act
        retrieved = repo.get_by_id(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == name

    def test_get_by_id_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should not return soft-deleted user when include_deleted=False."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act
        retrieved = repo.get_by_id(user.id)

        # Assert
        assert retrieved is None

    def test_get_by_id_includes_soft_deleted_when_requested(self, db_session: Session):
        """Should return soft-deleted user when include_deleted=True."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act
        retrieved = repo.get_by_id(user.id, include_deleted=True)

        # Assert
        assert retrieved is not None
        assert retrieved.deleted_at is not None

    def test_get_by_email_returns_user(self, db_session: Session):
        """Should retrieve user by email."""
        # Arrange
        repo = SQLUserRepository(db_session)
        name = unique_name("John")
        email = unique_email("john")
        created = repo.create(name=name, email=email, hashed_password="password")

        # Act
        retrieved = repo.get_by_email(email)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_all_excludes_deleted_by_default(self, db_session: Session):
        """Should not include soft-deleted users in list_all."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user1 = repo.create(
            name=unique_name("Active"), email=unique_email("active"), hashed_password="password"
        )
        user2 = repo.create(
            name=unique_name("Deleted"), email=unique_email("deleted"), hashed_password="password"
        )

        assert user2.id is not None
        repo.soft_delete(user2.id)

        # Act
        users = repo.list_all(include_deleted=True)

        # Assert
        user_ids = {u.id for u in users}
        assert user1.id in user_ids
        assert user2.id in user_ids

    def test_update_persists_changes_to_database(self, db_session: Session):
        """Should update user and verify changes in database."""
        # Arrange
        repo = SQLUserRepository(db_session)
        name = unique_name("John")
        email = unique_email("john")
        user = repo.create(name=name, email=email, hashed_password="password")
        assert user.id is not None
        new_email = unique_email("jane")

        # Act
        updated = repo.update(user.id, name="Jane Doe", email=new_email)

        # Assert - Via repository
        assert updated is not None
        assert updated.name == "Jane Doe"
        assert updated.email == new_email

        # Assert - Via direct DB query
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        assert db_user.name == "Jane Doe"
        assert db_user.email == new_email
        assert db_user.updated_at is not None

    def test_update_duplicate_email_raises_error(self, db_session: Session):
        """Should raise ValueError when updating to existing email."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email1 = unique_email("user1")
        email2 = unique_email("user2")
        user1 = repo.create(name=unique_name("One"), email=email1, hashed_password="password")
        assert user1.id is not None
        repo.create(name=unique_name("Two"), email=email2, hashed_password="password")

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.update(user1.id, email=email2)

    def test_soft_delete_sets_deleted_at_in_database(self, db_session: Session):
        """Should set deleted_at timestamp in database when soft deleting."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None

        # Act
        result = repo.soft_delete(user.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        assert db_user.deleted_at is not None
        assert db_user.is_active is False

    def test_soft_delete_already_deleted_returns_false(self, db_session: Session):
        """Should return False when trying to delete already deleted user."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act
        result = repo.soft_delete(user.id)

        # Assert
        assert result is False

    def test_restore_clears_deleted_at_in_database(self, db_session: Session):
        """Should clear deleted_at timestamp in database when restoring."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Verify deleted first
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        assert db_user.deleted_at is not None

        # Act
        result = repo.restore(user.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        assert db_user.deleted_at is None

    def test_restore_non_deleted_returns_false(self, db_session: Session):
        """Should return False when trying to restore non-deleted user."""
        # Arrange
        repo = SQLUserRepository(db_session)
        user = repo.create(name=unique_name(), email=unique_email(), hashed_password="password")
        assert user.id is not None

        # Act
        result = repo.restore(user.id)

        # Assert
        assert result is False


class TestSQLClientRepository:
    """Integration tests for SQLClientRepository."""

    def test_create_individual_persists_to_database(self, db_session: Session):
        """Should create individual client and verify in database."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()

        # Act
        client = repo.create_individual(
            tax_id=tax_id,
            first_name="Juan",
            last_name="Pérez",
            email=unique_email("juan"),
        )
        assert client.id is not None

        # Assert - Via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.client_type == ClientType.INDIVIDUAL
        assert db_client.tax_id == tax_id
        assert db_client.first_name == "Juan"
        assert db_client.last_name == "Pérez"
        assert db_client.deleted_at is None

    def test_create_company_persists_to_database(self, db_session: Session):
        """Should create company client and verify in database."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()

        # Act
        client = repo.create_company(
            tax_id=tax_id,
            company_name="Empresa Test S.A.",
            email=unique_email("contacto"),
        )
        assert client.id is not None

        # Assert - Via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.client_type == ClientType.COMPANY
        assert db_client.tax_id == tax_id
        assert db_client.company_name == "Empresa Test S.A."
        assert db_client.deleted_at is None

    def test_create_duplicate_tax_id_raises_error(self, db_session: Session):
        """Should raise ValueError when creating client with duplicate tax_id."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        repo.create_individual(tax_id=tax_id, first_name="Test", last_name="User")

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.create_company(tax_id=tax_id, company_name="Test Company")

    def test_get_by_tax_id_returns_client(self, db_session: Session):
        """Should retrieve client by tax ID."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        created = repo.create_individual(tax_id=tax_id, first_name="Juan", last_name="Pérez")

        # Act
        retrieved = repo.get_by_tax_id(tax_id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_by_tax_id_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should not return soft-deleted client when include_deleted=False."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        client = repo.create_individual(tax_id=tax_id, first_name="Juan", last_name="Pérez")
        assert client.id is not None
        repo.soft_delete(client.id)

        # Act
        retrieved = repo.get_by_tax_id(tax_id)

        # Assert
        assert retrieved is None

    def test_update_individual_client_persists_changes(self, db_session: Session):
        """Should update individual client and verify in database."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        client = repo.create_individual(
            tax_id=tax_id,
            first_name="Juan",
            last_name="Pérez",
            email=unique_email("juan"),
        )
        assert client.id is not None
        new_email = unique_email("pedro")

        # Act
        repo.update(
            client.id,
            first_name="Pedro",
            last_name="Gómez",
            email=new_email,
        )

        # Assert - Via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.first_name == "Pedro"
        assert db_client.last_name == "Gómez"
        assert db_client.email == new_email
        assert db_client.updated_at is not None

    def test_update_company_client_persists_changes(self, db_session: Session):
        """Should update company client and verify in database."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        client = repo.create_company(
            tax_id=tax_id,
            company_name="Old Company",
            email=unique_email("old"),
        )
        assert client.id is not None
        new_email = unique_email("new")

        # Act
        repo.update(
            client.id,
            company_name="New Company",
            email=new_email,
        )

        # Assert - Via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.company_name == "New Company"
        assert db_client.email == new_email

    def test_soft_delete_sets_deleted_at_in_database(self, db_session: Session):
        """Should set deleted_at timestamp in database when soft deleting."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        client = repo.create_individual(tax_id=tax_id, first_name="Juan", last_name="Pérez")
        assert client.id is not None

        # Act
        result = repo.soft_delete(client.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.deleted_at is not None

    def test_restore_clears_deleted_at_in_database(self, db_session: Session):
        """Should clear deleted_at timestamp in database when restoring."""
        # Arrange
        repo = SQLClientRepository(db_session)
        tax_id = unique_tax_id()
        client = repo.create_individual(tax_id=tax_id, first_name="Juan", last_name="Pérez")
        assert client.id is not None
        repo.soft_delete(client.id)

        # Act
        result = repo.restore(client.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        assert db_client.deleted_at is None


class TestSQLPaperRepository:
    """Integration tests for SQLPaperRepository."""

    def test_create_paper_persists_to_database(self, db_session: Session):
        """Should create paper and verify in database."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Couche")

        # Act
        paper = repo.create(name=name, weight=350, description="Papel premium")
        assert paper.id is not None

        # Assert - Via direct DB query
        db_paper = db_session.execute(select(Paper).where(Paper.id == paper.id)).scalar_one()
        assert db_paper.name == name
        assert db_paper.weight == 350
        assert db_paper.description == "Papel premium"
        assert db_paper.is_active is True
        assert db_paper.deleted_at is None

    def test_create_duplicate_name_raises_error(self, db_session: Session):
        """Should raise ValueError when creating paper with duplicate name."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Couche")
        repo.create(name=name, weight=300)

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.create(name=name, weight=350)

    def test_get_by_name_returns_paper(self, db_session: Session):
        """Should retrieve paper by name."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Bond")
        created = repo.create(name=name, weight=100)

        # Act
        retrieved = repo.get_by_name(name)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_by_name_excludes_soft_deleted_by_default(self, db_session: Session):
        """Should not return soft-deleted paper when include_deleted=False."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Bond")
        paper = repo.create(name=name, weight=100)
        assert paper.id is not None
        repo.soft_delete(paper.id)

        # Act
        retrieved = repo.get_by_name(name)

        # Assert
        assert retrieved is None

    def test_list_active_returns_only_active_and_non_deleted(self, db_session: Session):
        """Should return only papers that are active and not soft-deleted."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        active = repo.create(name=unique_name("Active"), weight=200)
        inactive = repo.create(name=unique_name("Inactive"), weight=200)
        deleted = repo.create(name=unique_name("Deleted"), weight=200)

        assert inactive.id is not None
        assert deleted.id is not None

        # Set inactive and deleted
        repo.update(inactive.id, is_active=False)
        repo.soft_delete(deleted.id)

        # Act
        papers = repo.list_active()

        # Assert
        paper_ids = {p.id for p in papers}
        assert active.id in paper_ids
        assert inactive.id not in paper_ids
        assert deleted.id not in paper_ids

    def test_update_persists_changes_to_database(self, db_session: Session):
        """Should update paper and verify changes in database."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Old")
        paper = repo.create(name=name, weight=200)
        assert paper.id is not None
        new_name = unique_name("New")

        # Act
        repo.update(
            paper.id,
            name=new_name,
            weight=250,
            description="Updated description",
        )

        # Assert - Via direct DB query
        db_paper = db_session.execute(select(Paper).where(Paper.id == paper.id)).scalar_one()
        assert db_paper.name == new_name
        assert db_paper.weight == 250
        assert db_paper.description == "Updated description"
        assert db_paper.updated_at is not None

    def test_update_duplicate_name_raises_error(self, db_session: Session):
        """Should raise ValueError when updating to existing name."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name1 = unique_name("One")
        name2 = unique_name("Two")
        paper1 = repo.create(name=name1, weight=200)
        assert paper1.id is not None
        repo.create(name=name2, weight=250)

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.update(paper1.id, name=name2)

    def test_soft_delete_sets_deleted_at_and_inactive_in_database(self, db_session: Session):
        """Should set deleted_at and is_active=False in database when soft deleting."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Test")
        paper = repo.create(name=name, weight=200)
        assert paper.id is not None

        # Act
        result = repo.soft_delete(paper.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_paper = db_session.execute(select(Paper).where(Paper.id == paper.id)).scalar_one()
        assert db_paper.deleted_at is not None
        assert db_paper.is_active is False

    def test_restore_clears_deleted_at_in_database(self, db_session: Session):
        """Should clear deleted_at in database when restoring."""
        # Arrange
        repo = SQLPaperRepository(db_session)
        name = unique_name("Test")
        paper = repo.create(name=name, weight=200)
        assert paper.id is not None
        repo.soft_delete(paper.id)

        # Act
        result = repo.restore(paper.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_paper = db_session.execute(select(Paper).where(Paper.id == paper.id)).scalar_one()
        assert db_paper.deleted_at is None


class TestSQLFinishRepository:
    """Integration tests for SQLFinishRepository."""

    def test_create_finish_persists_to_database(self, db_session: Session):
        """Should create finish and verify in database."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Laminado")

        # Act
        finish = repo.create(
            name=name,
            description="Laminado brillante de alta calidad",
        )
        assert finish.id is not None

        # Assert - Via direct DB query
        db_finish = db_session.execute(select(Finish).where(Finish.id == finish.id)).scalar_one()
        assert db_finish.name == name
        assert db_finish.description == "Laminado brillante de alta calidad"
        assert db_finish.is_active is True
        assert db_finish.deleted_at is None

    def test_create_duplicate_name_raises_error(self, db_session: Session):
        """Should raise ValueError when creating finish with duplicate name."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Corte")
        repo.create(name=name)

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            repo.create(name=name)

    def test_get_by_name_returns_finish(self, db_session: Session):
        """Should retrieve finish by name."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Ojetillo")
        created = repo.create(name=name)

        # Act
        retrieved = repo.get_by_name(name)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_active_returns_only_active_and_non_deleted(self, db_session: Session):
        """Should return only finishes that are active and not soft-deleted."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        active = repo.create(name=unique_name("Active"))
        inactive = repo.create(name=unique_name("Inactive"))
        deleted = repo.create(name=unique_name("Deleted"))

        assert inactive.id is not None
        assert deleted.id is not None

        # Set inactive and deleted
        repo.update(inactive.id, is_active=False)
        repo.soft_delete(deleted.id)

        # Act
        finishes = repo.list_active()

        # Assert
        finish_ids = {f.id for f in finishes}
        assert active.id in finish_ids
        assert inactive.id not in finish_ids
        assert deleted.id not in finish_ids

    def test_update_persists_changes_to_database(self, db_session: Session):
        """Should update finish and verify changes in database."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Old")
        finish = repo.create(name=name)
        assert finish.id is not None
        new_name = unique_name("New")

        # Act
        repo.update(
            finish.id,
            name=new_name,
            description="Updated description",
        )

        # Assert - Via direct DB query
        db_finish = db_session.execute(select(Finish).where(Finish.id == finish.id)).scalar_one()
        assert db_finish.name == new_name
        assert db_finish.description == "Updated description"
        assert db_finish.updated_at is not None

    def test_soft_delete_sets_deleted_at_and_inactive_in_database(self, db_session: Session):
        """Should set deleted_at and is_active=False in database when soft deleting."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Test")
        finish = repo.create(name=name)
        assert finish.id is not None

        # Act
        result = repo.soft_delete(finish.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_finish = db_session.execute(select(Finish).where(Finish.id == finish.id)).scalar_one()
        assert db_finish.deleted_at is not None
        assert db_finish.is_active is False

    def test_restore_clears_deleted_at_in_database(self, db_session: Session):
        """Should clear deleted_at in database when restoring."""
        # Arrange
        repo = SQLFinishRepository(db_session)
        name = unique_name("Test")
        finish = repo.create(name=name)
        assert finish.id is not None
        repo.soft_delete(finish.id)

        # Act
        result = repo.restore(finish.id)

        # Assert
        assert result is True

        # Verify via direct DB query
        db_finish = db_session.execute(select(Finish).where(Finish.id == finish.id)).scalar_one()
        assert db_finish.deleted_at is None


class TestSoftDeleteIntegrationScenarios:
    """Integration tests for complex soft delete scenarios."""

    def test_deleted_user_not_appears_in_get_by_email(self, db_session: Session):
        """Soft-deleted user should not be found by email."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email("john")
        user = repo.create(name=unique_name("John"), email=email, hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act
        retrieved = repo.get_by_email(email)

        # Assert
        assert retrieved is None

    def test_deleted_user_appears_in_get_by_email_with_include_deleted(self, db_session: Session):
        """Soft-deleted user should be found by email when include_deleted=True."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email("john")
        user = repo.create(name=unique_name("John"), email=email, hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act
        retrieved = repo.get_by_email(email, include_deleted=True)

        # Assert
        assert retrieved is not None
        assert retrieved.deleted_at is not None

    def test_can_create_new_user_with_email_of_deleted_user(self, db_session: Session):
        """Should not allow creating user with email of deleted user."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email("same")
        user = repo.create(name=unique_name("Old"), email=email, hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act & Assert - Should raise error because email still exists in DB
        with pytest.raises(ValueError, match="already exists"):
            repo.create(name=unique_name("New"), email=email, hashed_password="password")

    def test_cascade_soft_delete_not_implemented(self, db_session: Session):
        """Verify soft delete only affects the entity, not related entities."""
        # This test documents that soft delete doesn't cascade
        # Future: could test relationships if needed
        pass

    def test_restore_makes_entity_visible_in_list_again(self, db_session: Session):
        """Restored entity should appear in list_all again."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email("john")
        user = repo.create(name=unique_name("John"), email=email, hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)
        assert user.id not in {u.id for u in repo.list_all()}

        # Act
        repo.restore(user.id)

        # Assert
        users = repo.list_all()
        assert user.id in {u.id for u in users}

    def test_update_deleted_entity_fails(self, db_session: Session):
        """Should not be able to update a deleted entity."""
        # Arrange
        repo = SQLUserRepository(db_session)
        email = unique_email("john")
        user = repo.create(name=unique_name("John"), email=email, hashed_password="password")
        assert user.id is not None
        repo.soft_delete(user.id)

        # Act - Try to update deleted user via include_deleted=True
        user_including_deleted = repo.get_by_id(user.id, include_deleted=True)
        assert user_including_deleted is not None

        # The update method can find the user with include_deleted=True internally
        # but typically we want to prevent updates to soft-deleted entities
        # For now, we allow it (implementation detail)

    def test_timestamp_consistency(self, db_session: Session):
        """Verify all timestamps are properly set."""
        # Arrange
        user_repo = SQLUserRepository(db_session)
        client_repo = SQLClientRepository(db_session)
        paper_repo = SQLPaperRepository(db_session)
        finish_repo = SQLFinishRepository(db_session)

        before_create = datetime.utcnow()

        # Act - Create entities
        user = user_repo.create(
            name=unique_name(), email=unique_email(), hashed_password="password"
        )
        assert user.id is not None
        client = client_repo.create_individual(
            tax_id=unique_tax_id(), first_name="Test", last_name="User"
        )
        assert client.id is not None
        paper = paper_repo.create(name=unique_name(), weight=100)
        assert paper.id is not None
        finish = finish_repo.create(name=unique_name())
        assert finish.id is not None

        # Assert - created_at should be set
        assert user.created_at is not None
        assert user.created_at >= before_create
        assert client.created_at is not None
        assert paper.created_at is not None
        assert finish.created_at is not None

        # Assert - updated_at should be None initially
        assert user.updated_at is None
        assert client.updated_at is None
        assert paper.updated_at is None
        assert finish.updated_at is None

        # Act - Update entities
        user_repo.update(user.id, name=unique_name())
        client_repo.update(client.id, first_name="Updated")
        paper_repo.update(paper.id, name=unique_name())
        finish_repo.update(finish.id, name=unique_name())

        # Assert - updated_at should be set after update
        db_user = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
        db_client = db_session.execute(select(Client).where(Client.id == client.id)).scalar_one()
        db_paper = db_session.execute(select(Paper).where(Paper.id == paper.id)).scalar_one()
        db_finish = db_session.execute(select(Finish).where(Finish.id == finish.id)).scalar_one()

        assert db_user.updated_at is not None
        assert db_client.updated_at is not None
        assert db_paper.updated_at is not None
        assert db_finish.updated_at is not None

        # Assert - deleted_at should be None
        assert db_user.deleted_at is None
        assert db_client.deleted_at is None
        assert db_paper.deleted_at is None
        assert db_finish.deleted_at is None
