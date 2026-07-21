#!/usr/bin/env python3
"""Debug script for packing calculation."""

from quote.pricing.packing import PackingCalculator

calculator = PackingCalculator()

# Valores del test
piece_width_cm = 14
piece_height_cm = 21.5
sheet_width_cm = 66  # viene de standard_sizes
sheet_height_cm = 44
bleed_mm = 3
margin_mm = 5
gap_mm = 3
allow_rotate = True

print("=== CÁLCULO DE IMPOSICIÓN ===")
print(f"Pieza: {piece_width_cm} x {piece_height_cm} cm")
print(f"Pliego: {sheet_width_cm} x {sheet_height_cm} cm")
print(f"Márgenes: bleed={bleed_mm}mm, margin={margin_mm}mm, gap={gap_mm}mm")
print()

# Calcular manualmente
print("=== CÁLCULO MANUAL ===")
# Sin rotación
fit_w_normal = int(sheet_width_cm // piece_width_cm)
fit_h_normal = int(sheet_height_cm // piece_height_cm)
total_normal = fit_w_normal * fit_h_normal
print(f"Sin rotación: {fit_w_normal} x {fit_h_normal} = {total_normal}")

# Con rotación
fit_w_rot = int(sheet_width_cm // piece_height_cm)
fit_h_rot = int(sheet_height_cm // piece_width_cm)
total_rot = fit_w_rot * fit_h_rot
print(f"Con rotación: {fit_w_rot} x {fit_h_rot} = {total_rot}")
print()

# Usando el PackingCalculator
result = calculator.calculate_pieces_per_sheet(
    piece_width_cm=piece_width_cm,
    piece_height_cm=piece_height_cm,
    sheet_width_cm=sheet_width_cm,
    sheet_height_cm=sheet_height_cm,
    bleed_mm=bleed_mm,
    margin_mm=margin_mm,
    gap_mm=gap_mm,
    allow_rotate=allow_rotate,
)

print("=== RESULTADO PackingCalculator ===")
print(f"Piezas por pliego: {result}")
print()

# Según el ejemplo del usuario (60x46)
print("=== SEGÚN EJEMPLO DEL USUARIO (60x46) ===")
sheet_w_user = 60
sheet_h_user = 46
fit_w_user = int(sheet_w_user // piece_width_cm)  # 60/14 = 4
fit_h_user = int(sheet_h_user // piece_height_cm)  # 46/21.5 = 2
total_user = fit_w_user * fit_h_user
print(f"Con pliego 60x46: {fit_w_user} x {fit_h_user} = {total_user}")
