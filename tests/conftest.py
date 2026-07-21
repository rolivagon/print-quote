"""Test configuration and fixtures with isolated transactions.

This module provides test fixtures that use an in-memory database
with automatic transaction rollback for test isolation.
"""

import os
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from quote.domain.enums import (
    ClientType,
    ColorMode,
    PrintType,
    QuoteStatus,
    Unit,
    UserRole,
)
from quote.repo.models import (
    BaseMeasurement,
    Client,
    Finish,
    FinishPricing,
    Paper,
    PaperPricing,
    Quote,
    QuoteItem,
    SQLModel,
    User,
)

# Ensure we're in test mode
os.environ["PYTEST_CURRENT_TEST"] = "true"
os.environ["APP_ENV"] = "testing"


# Create engine for tests (in-memory SQLite)
@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a database session with automatic rollback.

    Each test runs in its own transaction that is rolled back at the end,
    ensuring test isolation. No data persists between tests.
    """
    # Start a connection
    connection = engine.connect()

    # Begin a transaction
    transaction = connection.begin()

    # Create a session bound to this connection
    session = Session(bind=connection)

    try:
        yield session
    finally:
        # Rollback the transaction (undo all changes)
        session.close()
        transaction.rollback()
        connection.close()


# ============================================================================
# Helper Functions for Creating Test Data
# ============================================================================


def create_test_user(
    session: Session,
    email: str | None = None,
    name: str = "Test User",
    role: UserRole = UserRole.VENDEDOR,
) -> User:
    """Create a test user with unique email."""
    if email is None:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        name=name,
        email=email,
        role=role,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def create_test_client(
    session: Session,
    client_type: ClientType = ClientType.COMPANY,
    email: str | None = None,
    tax_id: str | None = None,
    company_name: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> Client:
    """Create a test client."""
    if email is None:
        email = f"client_{uuid.uuid4().hex[:8]}@example.com"

    if tax_id is None:
        tax_id = f"{uuid.uuid4().hex[:8]}-K"

    if client_type == ClientType.COMPANY:
        client = Client(
            client_type=client_type,
            email=email,
            phone="+56912345678",
            address="Test Address 123",
            tax_id=tax_id,
            company_name=company_name or f"Test Company {uuid.uuid4().hex[:4]}",
        )
    else:
        client = Client(
            client_type=client_type,
            email=email,
            phone="+56987654321",
            address="Test Address 456",
            tax_id=tax_id,
            first_name=first_name or "John",
            last_name=last_name or "Doe",
        )

    session.add(client)
    session.flush()
    return client


def create_test_paper(
    session: Session,
    name: str | None = None,
    weight: int = 300,
) -> Paper:
    """Create a test paper."""
    if name is None:
        name = f"Couche {weight}g Test"

    paper = Paper(
        name=name,
        weight=weight,
        description=f"Papel de prueba {weight}g",
        is_active=True,
    )
    session.add(paper)
    session.flush()
    return paper


def create_test_paper_pricing(
    session: Session,
    paper_id: int,
    print_type: PrintType,
    min_quantity: int,
    max_quantity: int | None,
    unit_price: Decimal,
    color_mode: ColorMode | None = None,
) -> PaperPricing:
    """Create paper pricing for a test paper."""
    pricing = PaperPricing(
        paper_id=paper_id,
        print_type=print_type,
        color_mode=color_mode,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        unit_price=unit_price,
    )
    session.add(pricing)
    session.flush()
    return pricing


def create_test_finish(
    session: Session,
    name: str | None = None,
) -> Finish:
    """Create a test finish."""
    if name is None:
        name = f"Corte Test {uuid.uuid4().hex[:4]}"

    finish = Finish(
        name=name,
        description=f"Terminación de prueba: {name}",
        is_active=True,
    )
    session.add(finish)
    session.flush()
    return finish


def create_test_finish_pricing(
    session: Session,
    finish_id: int,
    print_type: PrintType,
    unit: Unit,
    min_quantity: int,
    max_quantity: int | None,
    unit_price: Decimal,
) -> FinishPricing:
    """Create finish pricing for a test finish."""
    pricing = FinishPricing(
        finish_id=finish_id,
        print_type=print_type,
        unit=unit,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        unit_price=unit_price,
    )
    session.add(pricing)
    session.flush()
    return pricing


def create_test_quote(
    session: Session,
    seller_id: int,
    client_id: int,
    quote_number: str | None = None,
) -> Quote:
    """Create a test quote."""
    if quote_number is None:
        quote_number = f"COT-TEST-{uuid.uuid4().hex[:8]}"

    quote = Quote(
        quote_number=quote_number,
        status=QuoteStatus.DRAFT,
        seller_id=seller_id,
        client_id=client_id,
        subtotal=Decimal("10000"),
        tax=Decimal("1900"),
        total=Decimal("11900"),
    )
    session.add(quote)
    session.flush()
    return quote


def create_test_quote_item(
    session: Session,
    quote_id: int,
    paper_id: int,
    name: str = "Test Item",
    quantity: int = 100,
) -> QuoteItem:
    """Create a test quote item."""
    item = QuoteItem(
        quote_id=quote_id,
        paper_id=paper_id,
        name=name,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        width=Decimal("21.0"),
        height=Decimal("29.7"),
        quantity=quantity,
        paper_unit_price=Decimal("500"),
    )
    session.add(item)
    session.flush()
    return item


# ============================================================================
# Fixtures for Common Test Data
# ============================================================================


@pytest.fixture
def test_user(db_session):
    """Create a basic test user."""
    return create_test_user(db_session)


@pytest.fixture
def test_client_company(db_session):
    """Create a test company client."""
    return create_test_client(db_session, client_type=ClientType.COMPANY)


@pytest.fixture
def test_client_individual(db_session):
    """Create a test individual client."""
    return create_test_client(db_session, client_type=ClientType.INDIVIDUAL)


@pytest.fixture
def test_paper_digital(db_session):
    """Create a test paper with digital pricing."""
    paper = create_test_paper(db_session, name="Couche 300g Digital")
    assert paper.id is not None

    # Add pricing for 4/4
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("715"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=101,
        max_quantity=500,
        unit_price=Decimal("650"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=501,
        max_quantity=None,
        unit_price=Decimal("580"),
    )

    # Add pricing for 4/0
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("550"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("500"),
    )

    return paper


@pytest.fixture
def test_finish_cut(db_session):
    """Create a test finish with pricing."""
    finish = create_test_finish(db_session, name="Corte Recto Test")
    assert finish.id is not None

    create_test_finish_pricing(
        session=db_session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("3000"),
    )
    create_test_finish_pricing(
        session=db_session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("5000"),
    )

    return finish


@pytest.fixture
def test_quote(db_session, test_user, test_client_company, test_paper_digital):
    """Create a test quote with all related data."""
    quote = create_test_quote(
        session=db_session,
        seller_id=test_user.id,
        client_id=test_client_company.id,
    )
    assert quote.id is not None

    create_test_quote_item(
        session=db_session,
        quote_id=quote.id,
        paper_id=test_paper_digital.id,
        name="Flyers Test",
        quantity=100,
    )

    return quote


# ============================================================================
# Legacy Fixtures (maintained for backward compatibility)
# ============================================================================


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for tests (legacy)."""
    return create_test_user(db_session, name="Sample Seller")


@pytest.fixture
def sample_client(db_session):
    """Create a sample client for tests (legacy)."""
    return create_test_client(db_session)


@pytest.fixture
def sample_paper(db_session):
    """Create a sample paper with pricing for tests (legacy)."""
    paper = create_test_paper(db_session, name="Bond 80g Test")
    assert paper.id is not None
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        min_quantity=1,
        max_quantity=None,
        unit_price=Decimal("500"),
    )
    return paper


@pytest.fixture
def sample_quote(db_session, sample_user, sample_client, sample_paper):
    """Create a sample quote for tests (legacy)."""
    return create_test_quote(
        session=db_session,
        seller_id=sample_user.id,
        client_id=sample_client.id,
    )


# ============================================================================
# Service Layer Fixtures (In-Memory Repositories)
# ============================================================================


from quote.repo.inmem import InMemoryFixedProductRepository, InMemoryQuoteRepository
from quote.service.quote_service import QuoteService


@pytest.fixture
def quote_repo():
    """Provide an in-memory quote repository for tests."""
    return InMemoryQuoteRepository()


@pytest.fixture
def fixed_product_repo():
    """Provide an in-memory fixed product repository for tests."""
    return InMemoryFixedProductRepository()


@pytest.fixture
def quote_service(quote_repo, fixed_product_repo):
    """Provide a quote service for tests."""
    return QuoteService(quote_repo, fixed_product_repo)


# ============================================================================
# Legacy seeded_db fixture for backward compatibility
# ============================================================================


@pytest.fixture
def seeded_db(db_session):
    """Provide a database session with seeded test data (legacy).

    Creates minimal test data needed for integration tests.
    Each test gets isolated data due to transaction rollback.
    """
    # Create test seller
    seller = create_test_user(
        session=db_session,
        name="Test Seller",
        email=f"seller_{uuid.uuid4().hex[:8]}@test.com",
        role=UserRole.SUPER_ADMIN,
    )

    # Create test client
    client = create_test_client(
        session=db_session,
        client_type=ClientType.COMPANY,
        email=f"company_{uuid.uuid4().hex[:8]}@test.com",
        tax_id=f"76.{uuid.uuid4().hex[:6]}-7",
    )

    # Create test paper with pricing
    paper = create_test_paper(db_session, name="Couche 300g Test")
    assert paper.id is not None

    # Add pricing ranges
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("715"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=101,
        max_quantity=500,
        unit_price=Decimal("650"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=501,
        max_quantity=None,
        unit_price=Decimal("580"),
    )

    # Add pricing for 4/0
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("550"),
    )
    create_test_paper_pricing(
        session=db_session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("500"),
    )

    # Create test finish
    finish = create_test_finish(db_session, name="Corte Recto Test")
    assert finish.id is not None

    create_test_finish_pricing(
        session=db_session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("3000"),
    )
    create_test_finish_pricing(
        session=db_session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("5000"),
    )

    # Create base measurements
    db_session.add_all(
        [
            BaseMeasurement(
                name="A4",
                width=Decimal("21.0"),
                height=Decimal("29.7"),
                description="Tamaño A4 estándar",
            ),
            BaseMeasurement(
                name="A3",
                width=Decimal("29.7"),
                height=Decimal("42.0"),
                description="Tamaño A3 estándar",
            ),
            BaseMeasurement(
                name="Carta",
                width=Decimal("21.6"),
                height=Decimal("27.9"),
                description="Tamaño carta",
            ),
        ]
    )

    return db_session, {
        "seller": seller,
        "client": client,
        "client_company": client,  # Alias for tests expecting this name
        "paper": paper,
        "paper_couche": paper,  # Alias for tests expecting this name
        "finish": finish,
        "finish_cut": finish,  # Alias for tests expecting this name
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def default_geometry():
    """Default geometry parameters for packing calculations."""
    return {"bleed_mm": 3, "margin_mm": 5, "gap_mm": 3, "allow_rotate": True}


@pytest.fixture
def financial_rules():
    """Global financial rules for calculations."""
    return {
        "vat_rate": Decimal("0.19"),
        "markup_by_category": {
            PrintType.DIGITAL: Decimal("0"),
            PrintType.PLOTTER: Decimal("0"),
            PrintType.OFFSET: Decimal("0"),
        },
        "rounding": "hundreds",
    }


@pytest.fixture
def standard_sizes():
    """Standard sizes for different print types."""
    return {
        "digital_sheet": {
            "width_cm": 30,
            "height_cm": 45,
            "usable_width_cm": 31,
            "usable_height_cm": 46,
        },
        "offset_sheet": {"width_cm": 66, "height_cm": 44},
        "plotter_minimum_m2": Decimal("0.25"),
    }


# ============================================================================
# Test Case Fixtures
# ============================================================================


@pytest.fixture
def flyer_500_case():
    """Test case for 500 flyers digital case."""
    return {
        "quantity": 500,
        "width_cm": 10,
        "height_cm": 15,
        "color_config": "4/0",
        "finishing": "corte_recto",
        "expected": {
            "pieces_per_sheet": 9,
            "sheets_needed": 56,
            "sheet_cost": Decimal("40040"),
            "finishing_cost": Decimal("3000"),
            "subtotal_before_markup": Decimal("43040"),
            "total_with_markup": Decimal("43040"),  # 0% markup
            "net_before_vat": Decimal("43000"),  # rounded
            "total_final": Decimal("51200"),  # 43040 * 1.19 = 51217.6 -> 51200
        },
    }


@pytest.fixture
def diploma_20_case():
    """Test case for 20 diplomas digital case with special price."""
    return {
        "quantity": 20,
        "width_cm": 21.5,
        "height_cm": 28,
        "color_config": "diploma_4/0",
        "finishing": None,
        "expected": {
            "pieces_per_sheet": 2,
            "sheets_needed": 10,
            "sheet_cost": Decimal("17600"),
            "subtotal_before_markup": Decimal("17600"),
        },
    }


@pytest.fixture
def tarjeta_300_case():
    """Test case for 300 business cards digital 4/4 color case."""
    return {
        "quantity": 300,
        "width_cm": 9,
        "height_cm": 5.5,
        "color_config": "4/4",
        "finishing": "corte_recto",
        "expected": {
            "pieces_per_sheet": 21,  # Calculated by PackingCalculator with bleed/margin/gap
            "sheets_needed": 15,  # ceil(300/21)
            "sheet_cost": Decimal("31350"),  # 15 sheets * $2,090 (price for range 11-20)
            "finishing_cost": Decimal("3000"),
            "subtotal_before_markup": Decimal("34350"),
        },
    }


@pytest.fixture
def afiche_plotter_case():
    """Test case for 70x50 cm plotter poster case."""
    return {
        "quantity": 1,
        "width_cm": 70,
        "height_cm": 50,
        "material": "sintetico",
        "finishing": "corte_recto",
        "expected": {
            "m2": Decimal("0.35"),
            "material_cost": Decimal("2975"),
            "finishing_cost": Decimal("1000"),
            "subtotal_before_markup": Decimal("3975"),
            # With 0% markup: 3975 * 1.19 = 4730.25 -> 4700
            "total_with_markup": Decimal("3975"),
            "net_before_vat": Decimal("4000"),  # rounded
            "total_final": Decimal("4700"),  # 3975 * 1.19 = 4730.25 -> 4700
        },
    }


@pytest.fixture
def lona_plotter_case():
    """Test case for 300x100 cm plotter banner case."""
    return {
        "quantity": 1,
        "width_cm": 300,
        "height_cm": 100,
        "material": "lona_pvc",
        "terminaciones": [
            {"tipo": "ojetillos", "cantidad": 6},
            {"tipo": "corte_recto", "cantidad": 1},
        ],
        "expected": {
            "m2": Decimal("3.0"),
            "material_cost": Decimal("25500"),
            "ojetillos_cost": Decimal("3000"),
        },
    }


@pytest.fixture
def digital_price_table():
    """Mock digital printing price table."""
    return {
        "4/0": [
            (1, 10, Decimal("1000")),
            (11, 50, Decimal("900")),
            (51, 100, Decimal("715")),
            (101, float("inf"), Decimal("650")),
        ],
        "4/4": [
            (1, 10, Decimal("2500")),
            (11, 20, Decimal("2090")),
            (21, 50, Decimal("2200")),
            (51, 100, Decimal("2090")),
            (101, float("inf"), Decimal("1900")),
        ],
        "diploma_4/0": [(1, float("inf"), Decimal("1760"))],
    }


@pytest.fixture
def digital_diploma_price():
    """Mock digital diploma price."""
    return Decimal("1760")


@pytest.fixture
def plotter_price_table():
    """Mock plotter printing price table."""
    return {
        "sintetico": Decimal("8500"),
        "lona_pvc": Decimal("8500"),
    }


@pytest.fixture
def offset_price_table():
    """Mock offset printing price table."""
    return {
        "planchas_por_color": Decimal("7000"),
        "tiraje": {
            1000: Decimal("50000"),
            2000: Decimal("80000"),
            5000: Decimal("170000"),
        },
        "terminaciones": {
            "troquel_por_1000": {
                1000: Decimal("70000"),
                5000: Decimal("60000"),
            }
        },
        "costos_fijos": {"molde_troquel": Decimal("20000")},
        "papel": {
            "couche_300g": Decimal("800000") / Decimal("5300"),
            "couche_170g": Decimal("33439"),
            "couche_250g": Decimal("26589"),
        },
    }


@pytest.fixture
def offset_5000_case():
    """Test case for 5000 units offset 4/0 case."""
    return {
        "cantidad": 5000,
        "width_cm": 55,
        "height_cm": 41.6,
        "color": "4/0",
        "terminacion": "troquel",
        "expected": {
            "pieces_per_sheet": 1,
            "merma_hojas": 300,
            "planchas_costo": Decimal("28000"),
            "tiraje_costo": Decimal("170000"),
            "terminacion_costo": Decimal("60000"),
            "molde_costo": Decimal("20000"),
            "subtotal_antes_markup": Decimal("1078000"),
            "markup_0_pct": Decimal("0"),  # 0% markup
            "subtotal_con_markup": Decimal("1078000"),  # No markup
            "total_final": Decimal("1282800"),  # 1078000 * 1.19 = 1282820 -> 1282800
        },
    }


@pytest.fixture
def offset_16000_volantes_case():
    """Test case for 16.000 volantes offset case."""
    return {
        "cantidad": 16000,
        "num_designs": 16,
        "num_runs": 2,
        "width_cm": 14,
        "height_cm": 21.5,
        "color": "4/4",
        "terminacion": "corte_recto",
        "expected": {
            "pieces_per_sheet": 8,
            "merma_hojas": 300,
            "total_sheets_with_merma": 2600,
            "planchas_costo": Decimal("112000"),
            "papel_costo": Decimal("200635"),
            "tiraje_costo": Decimal("140000"),
            "corte_costo": Decimal("10000"),
        },
    }


@pytest.fixture
def offset_finishing_prices():
    """Offset specific finishing prices."""
    return {
        "troquel": {"mode": "per_job", "price": Decimal("60000"), "molde": Decimal("20000")},
        "corte_recto": {"mode": "per_job", "price": Decimal("10000")},
        "corchete": {"mode": "per_job", "price": Decimal("55000")},
    }


@pytest.fixture
def offset_sheet_60x46():
    """Specific sheet size for 16.000 flyers case (60x46 cm)."""
    return {"width_cm": 60, "height_cm": 46}


@pytest.fixture
def offset_16000_volantes_completo_case():
    """Detailed test case for 16.000 volantes with complete breakdown."""
    return {
        "cantidad": 16000,
        "num_designs": 16,
        "num_runs": 2,
        "width_cm": 14,
        "height_cm": 21.5,
        "color": "4/4",
        "terminacion": "corte_recto",
        "expected": {
            "pieces_per_sheet": 8,
            "total_sheets_with_merma": 2600,
            "planchas_costo": Decimal("112000"),
            "papel_costo": Decimal("200635"),
            "papel_desglose": {
                "resma_size": "62x92",
                "hojas_por_resma": 250,
                "total_resmas": 6,
                "precio_por_resma": Decimal("33439.466666"),
            },
            "tiraje_costo": Decimal("140000"),
            "corte_costo": Decimal("10000"),
            "subtotal_antes_markup": Decimal("462635"),
            "markup_60_pct": Decimal("277581"),
            "total_con_markup": Decimal("740216"),
        },
    }


@pytest.fixture
def offset_950_revistas_case():
    """Detailed test case for 950 magazines."""
    return {
        "cantidad": 950,
        "paginas": 48,
        "cuartillas": 12,
        "width_extendido_cm": 43.2,
        "height_extendido_cm": 28,
        "width_cerrado_cm": 21.6,
        "height_cerrado_cm": 28,
        "color": "4/4",
        "papel_interior": "couche_170g",
        "papel_tapa": "couche_300g",
        "terminaciones": ["corchete", "corte"],
        "expected": {
            "cuartillas_por_pliego": 2,
            "total_tirajes_interior": 6,
            "total_tirajes_tapa": 1,
            "planchas_interior_costo": Decimal("336000"),
            "planchas_tapa_costo": Decimal("28000"),
            "papel_interior_costo": Decimal("501592"),
            "papel_tapa_costo": Decimal("106359"),
            "pliegos_interior": 3750,
            "pliegos_tapa": 1000,
            "tiraje_costo": Decimal("420000"),
            "corte_costo": Decimal("10000"),
            "corchete_costo": Decimal("55000"),
            "subtotal_antes_markup": Decimal("1456951"),
            "markup_60_pct": Decimal("874171"),
            "total_con_markup": Decimal("2331122"),
        },
    }


@pytest.fixture
def digital_finishing_prices():
    """Digital finishing prices."""
    return {"corte_recto": {"mode": "per_job", "price": Decimal("3000")}}


@pytest.fixture
def plotter_finishing_prices():
    """Plotter finishing prices."""
    return {
        "corte_recto": {"mode": "per_job", "price": Decimal("1000")},
        "ojetillos": {"mode": "per_quantity", "price": Decimal("500")},
    }


# ============================================================================
# API Testing Fixtures
# ============================================================================


import os

import pytest
from fastapi.testclient import TestClient

from quote.api.deps import get_current_user, get_db
from quote.api.main import app


class TestDBState:
    """Class to hold test database state between fixtures."""

    engine = None
    session = None
    SessionLocal = None
    connection = None
    transaction = None


def get_test_db_session_factory(state):
    """Create a get_db function that uses the shared test state."""

    def _get_db():
        # Create a new session for each request
        db = state.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return _get_db


@pytest.fixture
def api_test_state():
    """Provide a test database state that can be shared between fixtures.

    API tests run against the local Supabase PostgreSQL schema. A shared
    connection and outer transaction keep endpoint commits visible to the test
    while rolling all fixture data back afterward.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("requires local Supabase; run through make test-supabase")

    state = TestDBState()
    state.engine = create_engine(database_url, pool_pre_ping=True)
    state.connection = state.engine.connect()
    state.transaction = state.connection.begin()
    state.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=state.connection,
        join_transaction_mode="create_savepoint",
    )
    state.session = state.SessionLocal()

    yield state

    # Cleanup
    state.session.close()
    state.transaction.rollback()
    state.connection.close()
    state.engine.dispose()


def create_api_test_user(
    session: Session,
    *,
    name: str = "Test User",
    email: str | None = None,
    role: UserRole = UserRole.VENDEDOR,
) -> User:
    """Create an Auth-backed application profile for PostgreSQL API tests."""
    subject = uuid.uuid4()
    email = email or f"user_{subject.hex[:8]}@test.com"
    session.execute(
        text(
            "insert into auth.users "
            "(id, aud, role, email, encrypted_password, email_confirmed_at, "
            "raw_app_meta_data, raw_user_meta_data, created_at, updated_at) "
            "values (:id, 'authenticated', 'authenticated', :email, null, "
            'timezone(\'utc\', now()), \'{"provider":"email","providers":["email"]}\', '
            "cast(:metadata as jsonb), timezone('utc', now()), timezone('utc', now()))"
        ),
        {"id": str(subject), "email": email, "metadata": '{"name":"' + name + '"}'},
    )
    session.flush()
    user = session.get(User, subject)
    assert user is not None
    user.role = role
    session.flush()
    return user


@pytest.fixture
def api_user_factory(api_test_state):
    """Create Auth-backed profiles in the current API test transaction."""
    return lambda **kwargs: create_api_test_user(api_test_state.session, **kwargs)


@pytest.fixture
def api_client(api_test_state):
    """Provide a TestClient for API tests with overridden database.

    This fixture creates an isolated database for each test
    and makes it available through the get_test_db_session dependency.
    """
    # Override the get_db dependency
    app.dependency_overrides[get_db] = get_test_db_session_factory(api_test_state)

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(api_test_state):
    """Create an admin user for API tests.

    Creates the user directly in the api_client's database session.
    """
    user = create_api_test_user(
        api_test_state.session,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        role=UserRole.ADMIN,
    )
    api_test_state.session.commit()  # Commit so other sessions can see it
    api_test_state.session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Retained for API fixture compatibility; auth is overridden below."""
    return "test-supabase-token"


@pytest.fixture
def authorized_client(api_client, admin_token, admin_user):
    """Provide an authorized TestClient with Bearer token."""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    api_client.headers = {"Authorization": f"Bearer {admin_token}"}
    return api_client


@pytest.fixture
def api_test_user(api_test_state):
    """Create a regular user for API tests."""
    user = create_api_test_user(
        api_test_state.session,
        name="API Test User",
        email=f"user_{uuid.uuid4().hex[:8]}@test.com",
        role=UserRole.VENDEDOR,
    )
    api_test_state.session.commit()
    api_test_state.session.refresh(user)
    return user


@pytest.fixture
def api_seeded_db(api_test_state):
    """Provide seeded data for API tests in the api_test_state database.

    Creates test data needed for integration tests in the shared test database.
    """
    from quote.domain.enums import ClientType, ColorMode, PrintType, Unit
    from quote.repo.models import BaseMeasurement

    # Create test client
    client = create_test_client(
        session=api_test_state.session,
        client_type=ClientType.COMPANY,
        email=f"company_{uuid.uuid4().hex[:8]}@test.com",
        tax_id=f"76.{uuid.uuid4().hex[:6]}-7",
    )

    # Create test paper with pricing
    paper = create_test_paper(api_test_state.session, name="Couche 300g Test")
    assert paper.id is not None

    # Add pricing ranges for digital 4/4
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("715"),
    )
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=101,
        max_quantity=500,
        unit_price=Decimal("650"),
    )
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_4,
        min_quantity=501,
        max_quantity=None,
        unit_price=Decimal("580"),
    )

    # Add pricing for 4/0
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("550"),
    )
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        color_mode=ColorMode.C4_0,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("500"),
    )

    # Create test finish
    finish = create_test_finish(api_test_state.session, name="Corte Recto Test")
    assert finish.id is not None

    create_test_finish_pricing(
        session=api_test_state.session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=1,
        max_quantity=100,
        unit_price=Decimal("3000"),
    )
    create_test_finish_pricing(
        session=api_test_state.session,
        finish_id=finish.id,
        print_type=PrintType.DIGITAL,
        unit=Unit.JOB,
        min_quantity=101,
        max_quantity=None,
        unit_price=Decimal("5000"),
    )

    # Create base measurements
    api_test_state.session.add_all(
        [
            BaseMeasurement(
                name="A4",
                width=Decimal("21.0"),
                height=Decimal("29.7"),
                description="Tamaño A4 estándar",
            ),
            BaseMeasurement(
                name="A3",
                width=Decimal("29.7"),
                height=Decimal("42.0"),
                description="Tamaño A3 estándar",
            ),
            BaseMeasurement(
                name="Carta",
                width=Decimal("21.6"),
                height=Decimal("27.9"),
                description="Tamaño carta",
            ),
        ]
    )

    api_test_state.session.commit()

    return api_test_state.session, {
        "client": client,
        "client_company": client,  # Alias for tests expecting this name
        "paper": paper,
        "paper_couche": paper,  # Alias for tests expecting this name
        "finish": finish,
        "finish_cut": finish,  # Alias for tests expecting this name
    }


@pytest.fixture
def api_sample_user(api_test_state):
    """Create a sample user for API tests."""
    user = create_api_test_user(api_test_state.session, name="Sample API User")
    api_test_state.session.commit()
    api_test_state.session.refresh(user)
    return user


@pytest.fixture
def api_sample_client(api_test_state):
    """Create a sample client for API tests."""
    client = create_test_client(
        api_test_state.session,
        client_type=ClientType.COMPANY,
        email=f"api_client_{uuid.uuid4().hex[:8]}@test.com",
        tax_id=f"76.{uuid.uuid4().hex[:6]}-7",
    )
    api_test_state.session.commit()
    api_test_state.session.refresh(client)
    return client


@pytest.fixture
def api_sample_paper(api_test_state):
    """Create a sample paper with pricing for API tests."""
    paper = create_test_paper(api_test_state.session, name="Bond 80g API Test")
    assert paper.id is not None
    create_test_paper_pricing(
        session=api_test_state.session,
        paper_id=paper.id,
        print_type=PrintType.DIGITAL,
        min_quantity=1,
        max_quantity=None,
        unit_price=Decimal("500"),
    )
    api_test_state.session.commit()
    api_test_state.session.refresh(paper)
    return paper


@pytest.fixture
def api_sample_finish(api_test_state):
    """Create a sample finish for API tests."""
    finish = create_test_finish(
        api_test_state.session,
        name=f"API Finish Test {uuid.uuid4().hex[:8]}",
    )
    api_test_state.session.commit()
    api_test_state.session.refresh(finish)
    return finish
