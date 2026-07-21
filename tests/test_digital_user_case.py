from decimal import Decimal

from quote.pricing.digital import DigitalPricingStrategy
from quote.pricing.packing import PackingCalculator


def test_digital_tripticos_user_case():
    """
    Test case provided by the user:
    100 trípticos 21,5x28 cm
    Papel Couche 170g $880/pliego
    Plisado y doblado $5.000
    Corte $5.000
    10% pérdidas
    + IVA
    """
    strategy = DigitalPricingStrategy()
    calculator = PackingCalculator()

    # 1. Parámetros básicos
    qty = 100
    width_cm = 21.5
    height_cm = 28
    sheet_w = 31
    sheet_h = 46

    # 2. Configuración de precios
    # Usamos el nombre del papel como clave para simplificar el lookup en este test
    price_per_sheet = Decimal("880")
    price_table = {"couche_170g": [(1, 1000, price_per_sheet)]}

    finishing_prices = {
        "plisado_doblado": {"mode": "per_job", "price": Decimal("5000")},
        "corte": {"mode": "per_job", "price": Decimal("5000")},
    }

    loss_rate = Decimal("0.10")
    iva_rate = Decimal("0.19")

    # 3. Packing: ¿Cuántos caben? (Deberían ser 2)
    # 31/21.5 = 1.44 -> 1
    # 46/28 = 1.64 -> 1
    # Rotado:
    # 31/28 = 1.1 -> 1
    # 46/21.5 = 2.13 -> 2  <-- Cabe 1x2 = 2
    pieces_per_sheet = calculator.calculate_pieces_per_sheet(
        piece_width_cm=width_cm,
        piece_height_cm=height_cm,
        sheet_width_cm=sheet_w,
        sheet_height_cm=sheet_h,
        bleed_mm=0,
        margin_mm=0,
        gap_mm=0,
        allow_rotate=True,
    )
    assert pieces_per_sheet == 2

    # 4. Pliegos necesarios: 100 / 2 = 50
    sheets_needed = int(calculator.calculate_sheets_needed(qty, pieces_per_sheet))
    assert sheets_needed == 50

    # 5. Costo material: 50 * 880 = 44000
    material_cost = strategy.calculate_sheet_cost(sheets_needed, "couche_170g", price_table)
    assert material_cost == Decimal("44000")

    # 6. Costo terminaciones: 5000 + 5000 = 10000
    cost_plisado = strategy.calculate_finishing_cost("plisado_doblado", qty, finishing_prices)
    cost_corte = strategy.calculate_finishing_cost("corte", qty, finishing_prices)
    total_finishing = cost_plisado + cost_corte
    assert total_finishing == Decimal("10000")

    # 7. Subtotal: 44000 + 10000 = 54000
    subtotal = material_cost + total_finishing
    assert subtotal == Decimal("54000")

    # 8. Agregar 10% pérdidas: 54000 * 1.10 = 59400
    net_with_losses = strategy.apply_markup(subtotal, loss_rate)
    assert net_with_losses == Decimal("59400")

    # 9. Total con IVA: 59400 * 1.19 = 70686
    total_with_iva = strategy.apply_iva(net_with_losses, iva_rate)
    assert total_with_iva == Decimal("70686")

    # 10. Redondeo final a centenas: 70700
    final_total = strategy.round_to_hundreds(total_with_iva)
    assert final_total == Decimal("70700")
