"""Quote item input for MCP tools, normalized like the quote creation view."""

from pydantic import Field

from quote.api.schemas import QuoteItemCreate, SheetConfig
from quote.domain.enums import ColorMode, PrintType

# Mirrors DEFAULT_SHEET_CONFIGS in frontend/src/constants/index.ts.
DEFAULT_SHEET_CONFIGS = {
    PrintType.DIGITAL: SheetConfig(usable_width_cm=31, usable_height_cm=46),
    PrintType.OFFSET: SheetConfig(usable_width_cm=60, usable_height_cm=46),
}


class QuoteItemInput(QuoteItemCreate):
    """Quote item accepted by MCP tools.

    Same shape as the API payload, except that `color_mode` is optional for plotter items
    and `sheet_config` falls back to the quote view defaults.
    """

    color_mode: ColorMode | None = Field(
        None, description="Color mode (4/0, 4/4); required for digital and offset"
    )


def normalize_item(item: QuoteItemInput, material_name: str | None) -> QuoteItemCreate:
    """Return the API item the quote view would send for this input.

    `material_name` is the name of the plotter material selected by `paper_id`, if any.
    """
    data = item.model_dump(exclude={"color_mode", "sheet_config", "material_type"})
    if item.print_type == PrintType.PLOTTER:
        material_type = item.material_type or material_name
        if not material_type:
            raise ValueError("Plotter items require a material: paper_id or material_type")
        return QuoteItemCreate(
            **data, color_mode=ColorMode.C4_0, material_type=material_type, sheet_config=None
        )

    if item.color_mode is None:
        raise ValueError(f"color_mode is required for {item.print_type.value} items")
    if item.paper_id is None:
        raise ValueError(f"paper_id is required for {item.print_type.value} items")
    return QuoteItemCreate(
        **data,
        color_mode=item.color_mode,
        material_type=item.material_type,
        sheet_config=item.sheet_config or DEFAULT_SHEET_CONFIGS[item.print_type],
    )
