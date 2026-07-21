"""Tests for SQL repositories using TDD."""

from decimal import Decimal

from sqlalchemy.orm import Session

from quote.domain.enums import ClientType, PrintType, Unit
from quote.repo.models import (
    BaseMeasurement,
    Finish,
    FinishPricing,
    Paper,
    PaperPricing,
)
from quote.repo.sql_repo import SQLClientRepository, SQLMasterRepository


class TestSQLMasterRepositoryPaperPricing:
    """TDD tests for paper pricing queries."""

    def test_get_paper_price_exact_range_match(self, db_session: Session):
        """Should return price when quantity is within a defined range."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        # Create test paper with pricing
        paper = Paper(name="Test Paper", weight=200, is_active=True)
        db_session.add(paper)
        db_session.flush()

        # Add pricing: 1-100 sheets = $100 each
        pricing = PaperPricing(
            paper_id=paper.id,  # type: ignore[arg-type]
            print_type=PrintType.DIGITAL,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("100"),
        )
        db_session.add(pricing)
        db_session.commit()

        # Act
        result = repo.get_paper_price(paper.id, PrintType.DIGITAL, 50)

        # Assert
        assert result is not None
        assert result.unit_price == Decimal("100")

    def test_get_paper_price_unlimited_upper_range(self, db_session: Session):
        """Should return price when quantity is in range with no upper limit."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        paper = Paper(name="Test Paper", weight=200, is_active=True)
        db_session.add(paper)
        db_session.flush()

        # Add pricing: 101+ sheets = $80 each (no upper limit)
        pricing = PaperPricing(
            paper_id=paper.id,  # type: ignore[arg-type]
            print_type=PrintType.DIGITAL,
            min_quantity=101,
            max_quantity=None,
            unit_price=Decimal("80"),
        )
        db_session.add(pricing)
        db_session.commit()

        # Act
        result = repo.get_paper_price(paper.id, PrintType.DIGITAL, 500)

        # Assert
        assert result is not None
        assert result.unit_price == Decimal("80")

    def test_get_paper_price_out_of_range(self, db_session: Session):
        """Should return None when quantity is outside all ranges."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        paper = Paper(name="Test Paper", weight=200, is_active=True)
        db_session.add(paper)
        db_session.flush()

        # Add pricing: only 1-100 range
        pricing = PaperPricing(
            paper_id=paper.id,  # type: ignore[arg-type]
            print_type=PrintType.DIGITAL,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("100"),
        )
        db_session.add(pricing)
        db_session.commit()

        # Act
        result = repo.get_paper_price(paper.id, PrintType.DIGITAL, 150)

        # Assert
        assert result is None

    def test_get_paper_price_different_print_types(self, db_session: Session):
        """Should return different prices for same paper but different print types."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        paper = Paper(name="Test Paper", weight=300, is_active=True)
        db_session.add(paper)
        db_session.flush()

        # Digital pricing
        db_session.add(
            PaperPricing(
                paper_id=paper.id,  # type: ignore[arg-type]
                print_type=PrintType.DIGITAL,
                min_quantity=1,
                max_quantity=None,
                unit_price=Decimal("500"),
            )
        )

        # Offset pricing
        db_session.add(
            PaperPricing(
                paper_id=paper.id,  # type: ignore[arg-type]
                print_type=PrintType.OFFSET,
                min_quantity=1,
                max_quantity=None,
                unit_price=Decimal("150"),
            )
        )
        db_session.commit()

        # Act
        digital_price = repo.get_paper_price(paper.id, PrintType.DIGITAL, 10)
        offset_price = repo.get_paper_price(paper.id, PrintType.OFFSET, 10)

        # Assert
        assert digital_price is not None
        assert offset_price is not None
        assert digital_price.unit_price == Decimal("500")
        assert offset_price.unit_price == Decimal("150")


class TestSQLMasterRepositoryFinishPricing:
    """TDD tests for finish pricing queries."""

    def test_get_finish_price_exact_range(self, db_session: Session):
        """Should return finish price for exact range match."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        finish = Finish(name="Corte", is_active=True)
        db_session.add(finish)
        db_session.flush()

        pricing = FinishPricing(
            finish_id=finish.id,  # type: ignore[arg-type]
            print_type=PrintType.DIGITAL,
            unit=Unit.JOB,
            min_quantity=1,
            max_quantity=100,
            unit_price=Decimal("3000"),
        )
        db_session.add(pricing)
        db_session.commit()

        # Act
        result = repo.get_finish_price(finish.id, PrintType.DIGITAL, 50)

        # Assert
        assert result is not None
        assert result.unit_price == Decimal("3000")


class TestSQLClientRepository:
    """TDD tests for client repository."""

    def test_create_and_get_individual_client(self, db_session: Session):
        """Should create and retrieve an individual client."""
        # Arrange
        repo = SQLClientRepository(db_session)

        # Act
        import uuid

        unique_tax_id = f"{uuid.uuid4().hex[:8]}.123.456-7"
        client = repo.create_individual(
            tax_id=unique_tax_id,
            first_name="Juan",
            last_name="Pérez",
            email=f"juan_{uuid.uuid4().hex[:8]}@test.com",
            phone="+56912345678",
        )

        # Assert
        assert client.id is not None
        assert client.client_type == ClientType.INDIVIDUAL
        assert client.first_name == "Juan"
        assert client.last_name == "Pérez"

        # Verify retrieval
        retrieved = repo.get_by_id(client.id)
        assert retrieved is not None
        assert retrieved.first_name == "Juan"

    def test_create_and_get_company_client(self, db_session: Session):
        """Should create and retrieve a company client."""
        # Arrange
        repo = SQLClientRepository(db_session)

        # Act
        import uuid

        unique_tax_id = f"{uuid.uuid4().hex[:8]}.987.654-3"
        client = repo.create_company(
            tax_id=unique_tax_id,
            company_name="Empresa Test S.A.",
            email=f"contacto_{uuid.uuid4().hex[:8]}@empresa.cl",
            phone="+56987654321",
        )

        # Assert
        assert client.id is not None
        assert client.client_type == ClientType.COMPANY
        assert client.company_name == "Empresa Test S.A."

        # Verify retrieval
        retrieved = repo.get_by_id(client.id)
        assert retrieved is not None
        assert retrieved.company_name == "Empresa Test S.A."

    def test_get_by_tax_id(self, db_session: Session):
        """Should find client by tax ID."""
        # Arrange
        import uuid

        repo = SQLClientRepository(db_session)
        unique_tax_id = f"{uuid.uuid4().hex[:8]}.111.222-3"
        client = repo.create_individual(tax_id=unique_tax_id, first_name="Test", last_name="User")

        # Act
        result = repo.get_by_tax_id(unique_tax_id)

        # Assert
        assert result is not None
        assert result.id == client.id
        assert result.first_name == "Test"

    def test_get_by_tax_id_not_found(self, db_session: Session):
        """Should return None when tax ID not found."""
        # Arrange
        repo = SQLClientRepository(db_session)

        # Act
        result = repo.get_by_tax_id("99.999.999-9")

        # Assert
        assert result is None

    def test_list_all_clients(self, db_session: Session):
        """Should list all clients including newly created ones."""
        # Arrange
        repo = SQLClientRepository(db_session)
        initial_count = len(repo.list_all())

        # Create new clients
        repo.create_individual(tax_id="1-1", first_name="Ana", last_name="García")
        repo.create_company(tax_id="7-1", company_name="Beta Ltda.")

        # Act
        clients = repo.list_all()

        # Assert
        assert len(clients) == initial_count + 2


class TestSQLMasterRepositoryAdditionalQueries:
    """Additional tests for master repository queries."""

    def test_get_all_active_papers(self, db_session: Session):
        """Should return only active papers."""
        # Arrange
        repo = SQLMasterRepository(db_session)
        initial_active_count = len(repo.get_all_active_papers())

        active_paper = Paper(name="Active Paper Unique", weight=200, is_active=True)
        inactive_paper = Paper(name="Inactive Paper Unique", weight=200, is_active=False)
        db_session.add_all([active_paper, inactive_paper])
        db_session.commit()

        # Act
        papers = repo.get_all_active_papers()

        # Assert
        assert len(papers) == initial_active_count + 1
        active_names = [p.name for p in papers]
        assert "Active Paper Unique" in active_names
        assert "Inactive Paper Unique" not in active_names

    def test_get_all_active_finishes(self, db_session: Session):
        """Should return only active finishes."""
        # Arrange
        repo = SQLMasterRepository(db_session)
        initial_active_count = len(repo.get_all_active_finishes())

        active_finish = Finish(name="Corte Test", is_active=True)
        inactive_finish = Finish(name="Laminado Test", is_active=False)
        db_session.add_all([active_finish, inactive_finish])
        db_session.commit()

        # Act
        finishes = repo.get_all_active_finishes()

        # Assert
        assert len(finishes) == initial_active_count + 1
        finish_names = [f.name for f in finishes]
        assert "Corte Test" in finish_names
        assert "Laminado Test" not in finish_names

    def test_get_base_measurements(self, db_session: Session):
        """Should return all base measurements."""
        # Arrange
        repo = SQLMasterRepository(db_session)

        db_session.add_all(
            [
                BaseMeasurement(name="A4", width=Decimal("21.0"), height=Decimal("29.7")),
                BaseMeasurement(name="A3", width=Decimal("29.7"), height=Decimal("42.0")),
            ]
        )
        db_session.commit()

        # Act
        measurements = repo.get_all_base_measurements()

        # Assert
        assert len(measurements) == 2
        names = {m.name for m in measurements}
        assert names == {"A4", "A3"}
