"""Domain enums for print quote calculations."""

from enum import Enum


class PrintType(Enum):
    """Print type enumeration."""

    DIGITAL = "digital"
    OFFSET = "offset"
    PLOTTER = "plotter"


class PackingType(Enum):
    """Packing type enumeration."""

    STANDARD = "standard"
    PREMIUM = "premium"


class QuoteStatus(Enum):
    """Quote status enumeration."""

    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"


class ClientType(Enum):
    """Client type enumeration."""

    INDIVIDUAL = "individual"
    COMPANY = "company"


class ColorMode(Enum):
    """Color mode enumeration."""

    C4_0 = "4/0"
    C4_4 = "4/4"


class FinishType(Enum):
    """Finish type enumeration."""

    CUT = "cut"
    TROQUEL = "troquel"
    LAMINADO = "laminado"
    OJETILLO = "ojetillo"


class Unit(Enum):
    """Unit enumeration."""

    SHEET = "sheet"
    SQM = "sqm"
    PER_1000 = "per_1000"
    JOB = "job"
    PER_ITEM = "per_item"


class FinishingMode(Enum):
    """Finishing price calculation mode."""

    PER_JOB = "per_job"
    PER_QUANTITY = "per_quantity"
    PER_1000 = "per_1000"
    PER_LINEAR_METER = "per_linear_meter"


class UserRole(Enum):
    """User role enumeration for access control."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VENDEDOR = "vendedor"
