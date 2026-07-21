from decimal import Decimal

from quote.pricing.plotter import PlotterPricingStrategy


def test_plotter_afiches_sintetico_user_case():
    """
    Test case provided by the user:
    5 afiches 70x50
    Papel sintético $10.000/m2
    Corte recto $5.000
    10% pérdidas
    + IVA
    """
    strategy = PlotterPricingStrategy()

    # 1. Dimensions and quantity
    qty = 5
    width_cm = 70
    height_cm = 50

    # 2. Material and Finishing prices
    price_m2 = Decimal("10000")
    cut_price = Decimal("5000")
    loss_rate = Decimal("0.10")
    iva_rate = Decimal("0.19")

    price_table = {"sintetico": price_m2}
    finishing_table = {"corte_recto": {"mode": "per_job", "price": cut_price}}

    # 3. Calculate Area: 0.70 * 0.50 = 0.35 m2
    m2_unit = strategy.calculate_square_meters(width_cm, height_cm)
    assert m2_unit == Decimal("0.35")

    # 4. Material cost per unit: 0.35 * 10000 = 3500
    material_cost_unit = strategy.calculate_material_cost(m2_unit, "sintetico", price_table)
    assert material_cost_unit == Decimal("3500")

    # 5. Total material cost: 3500 * 5 = 17500
    total_material_cost = material_cost_unit * qty
    assert total_material_cost == Decimal("17500")

    # 6. Sum finishing (corte recto): 17500 + 5000 = 22500
    finishing_cost = strategy.calculate_finishing_cost("corte_recto", qty, finishing_table)
    assert finishing_cost == Decimal("5000")

    subtotal = total_material_cost + finishing_cost
    assert subtotal == Decimal("22500")

    # 7. Add 10% losses: 22500 * 1.10 = 24750
    net_with_losses = strategy.apply_markup(subtotal, loss_rate)
    assert net_with_losses == Decimal("24750")

    # 8. Total with IVA: 24750 * 1.19 = 29452.5
    total_with_iva = strategy.apply_iva(net_with_losses, iva_rate)
    assert total_with_iva == Decimal("29452.5")

    # 9. Round to hundreds: 29500
    final_total = strategy.round_to_hundreds(total_with_iva)
    assert final_total == Decimal("29500")
