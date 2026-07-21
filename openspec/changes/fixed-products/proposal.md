# Proposal: Fixed Products (Productos Fijos)

## Problem Statement
Los administradores necesitan crear productos pre-configurados con rangos de precio fijos que los vendedores puedan cotizar directamente, sin pasar por el cálculo detallado cada vez.

## User Story
Como **administrador**, quiero guardar una configuración de cotización como "Producto Fijo" con rangos de precio, para que los vendedores puedan cotizarlo rápidamente usando solo la cantidad.

## Scope
- ✅ Crear producto fijo desde pantalla de cotización
- ✅ Administrar productos fijos (CRUD)
- ✅ Gestionar rangos de precio por producto
- ✅ Cotizar usando producto fijo (quantity → price lookup)
- ❌ Importar/exportar productos
- ❌ Versionado de productos

## Success Criteria
1. Admin puede crear producto fijo desde cotización en < 3 clicks
2. Vendedor puede cotizar usando producto fijo en < 5 segundos
3. Rangos de precio no pueden superponerse
4. Precio se calcula como: quantity × unit_price (del rango aplicable)

## Pre-flight Check
- [x] User Persona: Admin crea, vendedores usan
- [x] Edge Cases: Rangos no superpuestos, cantidad fuera de rango
- [x] Data Impact: Nuevos modelos FixedProduct, FixedProductQuantityRange
- [x] TDD: test_create_fixed_product_from_quote
