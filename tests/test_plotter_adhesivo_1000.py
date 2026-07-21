from decimal import Decimal

from quote.pricing.plotter import PlotterPricingStrategy


def test_plotter_adhesivo_1000_units():
    """
    Test case provided by the user:
    1000 adhesivo de 10x15 cms
    Corte recto
    M2 de adhesivo $12.000
    Corte = $20 c/u
    Total $200.000 + 10% = $220.000 + iva
    """
    strategy = PlotterPricingStrategy()

    # 1. Dimensions and quantity
    qty = 1000
    width_cm = 10
    height_cm = 15

    # 2. Material and Finishing prices
    price_m2 = Decimal("12000")
    cut_unit_price = Decimal("20")
    loss_rate = Decimal("0.10")
    iva_rate = Decimal("0.19")

    price_table = {"adhesivo": price_m2}
    # For this case, corte_recto is "per_quantity" ($20 each)
    finishing_table = {"corte_recto": {"mode": "per_quantity", "price": cut_unit_price}}

    # 3. Calculate Area: 0.10 * 0.15 = 0.015 m2
    m2_unit = strategy.calculate_square_meters(width_cm, height_cm)
    assert m2_unit == Decimal("0.015")

    # 4. Material cost per unit: 0.015 * 12000 = 180
    material_cost_unit = strategy.calculate_material_cost(m2_unit, "adhesivo", price_table)
    assert material_cost_unit == Decimal("180")

    # 5. Total material cost: 180 * 1000 = 180000
    total_material_cost = material_cost_unit * qty
    assert total_material_cost == Decimal("180000")

    # 6. Sum finishing (corte recto por cantidad): 20 * 1000 = 20000
    finishing_cost = strategy.calculate_finishing_cost("corte_recto", qty, finishing_table)
    assert finishing_cost == Decimal("20000")

    subtotal = total_material_cost + finishing_cost
    assert subtotal == Decimal("200000")

    # 7. Add 10% losses: 200000 * 1.10 = 220000
    net_with_losses = strategy.apply_markup(subtotal, loss_rate)
    assert net_with_losses == Decimal("220000")

    # 8. Total with IVA: 220000 * 1.19 = 261800
    total_with_iva = strategy.apply_iva(net_with_losses, iva_rate)
    assert total_with_iva == Decimal("261800")

    # 9. Round to hundreds: 261800 (already rounded)
    final_total = strategy.round_to_hundreds(total_with_iva)
    assert final_total == Decimal("261800")
