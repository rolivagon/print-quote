"""Tests for MCP quote item normalization."""

import pytest

from quote.domain.enums import ColorMode, PrintType
from quote.mcp.items import QuoteItemInput, normalize_item


def _item(**overrides) -> QuoteItemInput:
    data = {
        "name": "Flyers",
        "print_type": "digital",
        "color_mode": "4/0",
        "quantity": 100,
        "width_cm": 10,
        "height_cm": 15,
        "paper_id": 1,
    }
    data.update(overrides)
    return QuoteItemInput.model_validate(data)


@pytest.mark.parametrize(
    ("print_type", "width", "height"),
    [("digital", 31, 46), ("offset", 60, 46)],
)
def test_missing_sheet_config_uses_quote_view_defaults(print_type, width, height):
    """Digital and offset items without sheet_config use the quote view defaults."""
    item = normalize_item(_item(print_type=print_type), material_name=None)

    assert item.sheet_config is not None
    assert (item.sheet_config.usable_width_cm, item.sheet_config.usable_height_cm) == (
        width,
        height,
    )


def test_explicit_sheet_config_is_kept():
    """An explicit sheet configuration overrides the defaults."""
    item = normalize_item(
        _item(sheet_config={"usable_width_cm": 32, "usable_height_cm": 45}), material_name=None
    )

    assert (item.sheet_config.usable_width_cm, item.sheet_config.usable_height_cm) == (32, 45)


def test_plotter_item_uses_4_0_and_resolves_material_from_paper():
    """Plotter items force 4/0 and take material_type from the selected material name."""
    item = normalize_item(
        _item(print_type="plotter", color_mode=None, paper_id=7), material_name="Lona PVC"
    )

    assert item.print_type == PrintType.PLOTTER
    assert item.color_mode == ColorMode.C4_0
    assert item.material_type == "Lona PVC"
    assert item.sheet_config is None


def test_plotter_explicit_material_type_is_kept():
    """An explicit plotter material_type is not replaced."""
    item = normalize_item(
        _item(print_type="plotter", paper_id=None, material_type="sintetico"),
        material_name=None,
    )

    assert item.material_type == "sintetico"


@pytest.mark.parametrize("print_type", ["digital", "offset"])
def test_sheet_item_requires_color_mode(print_type):
    """Digital and offset items cannot be priced without a color mode."""
    with pytest.raises(ValueError, match="color_mode"):
        normalize_item(_item(print_type=print_type, color_mode=None), material_name=None)


@pytest.mark.parametrize("print_type", ["digital", "offset"])
def test_sheet_item_requires_paper(print_type):
    """Digital and offset items cannot be priced without a paper."""
    with pytest.raises(ValueError, match="paper_id"):
        normalize_item(_item(print_type=print_type, paper_id=None), material_name=None)


def test_plotter_item_requires_material():
    """Plotter items need a material from paper_id or material_type."""
    with pytest.raises(ValueError, match="material"):
        normalize_item(_item(print_type="plotter", paper_id=None), material_name=None)
