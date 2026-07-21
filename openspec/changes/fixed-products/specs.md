# Specifications: Fixed Products

## API Endpoints

### POST /api/fixed-products/from-quote
Crear producto fijo desde cotización existente. El producto se crea sin rangos de precio inicialmente.

**Request:**
```json
{
  "product_id": "roller-80x200-sintetico",
  "name": "Roller 80x200 Sintético",
  "client_id": null,
  "quote_data": {
    "print_type": "digital",
    "quantity": 100,
    "width_cm": 80.0,
    "height_cm": 200.0,
    "paper_id": 5,
    "color_mode": "4/0",
    "finishes": [1],
    "sheet_config": {...},
    "geometry": {...}
  }
}
```

**Response 201:** FixedProduct creado (sin rangos inicialmente)

### GET /api/fixed-products
Listar productos. Query: `client_id`, `print_type`, `include_globals`

### GET /api/fixed-products/{id}
Obtener detalle del producto (incluye rangos si existen)

### POST /api/fixed-products/{id}/ranges
Agregar nuevo rango de precio al producto.

**Request:**
```json
{
  "min_qty": 1,
  "max_qty": 3,
  "unit_price": 38500
}
```

### PUT /api/fixed-products/{id}/ranges/{range_id}
Actualizar un rango existente.

**Request:**
```json
{
  "min_qty": 1,
  "max_qty": 5,
  "unit_price": 35000
}
```

### DELETE /api/fixed-products/{id}/ranges/{range_id}
Eliminar un rango específico.

### DELETE /api/fixed-products/{id}
Eliminar producto completo (cascada a rangos)

### GET /api/fixed-products/{id}/quote?quantity={n}
Cotizar usando producto fijo. Response: total, rango aplicado, metadatos

## Data Models

### SQLModel: FixedProduct
- id: UUID (PK)
- product_id: str (unique)
- name: str
- print_type: Enum(DIGITAL, OFFSET, PLOTTER)
- client_id: UUID (FK, nullable, default null) - null = producto global
- base_quote_snapshot: JSON
- is_active: bool
- created_at: datetime
- updated_at: datetime

### SQLModel: FixedProductQuantityRange
- id: UUID (PK)
- fixed_product_id: UUID (FK)
- min_quantity: int
- max_quantity: int
- unit_price: Decimal(15,2)

### Constraints
- product_id UNIQUE
- (fixed_product_id, min_quantity, max_quantity) UNIQUE
- No overlapping ranges per product
- FK to clients.id (nullable)

## Business Logic

### Creating Fixed Product
1. Receive quote_data (same as quote creation)
2. Calculate base quote to get pieces_per_sheet, costs
3. Store snapshot in base_quote_snapshot JSON
4. Create FixedProduct record (without ranges initially)
5. Return created product

### Managing Price Ranges (Pantalla de Detalle)
Después de crear el producto, el admin debe ir a la pantalla de detalle para agregar rangos:
1. Listar productos fijos
2. Seleccionar producto → ir a pantalla de detalle
3. Agregar/editar/eliminar rangos de precio (similar a Papers/Finishes)
4. Validar que rangos no se superpongan

### Quoting with Fixed Product
1. Find product by ID
2. Validate quantity is within defined ranges
3. Find applicable range
4. Calculate: total = quantity × unit_price
5. Return result with range metadata and reference data

## Validation Rules
- Ranges cannot overlap (e.g., 1-10 and 5-15 invalid)
- Quantity must be within a defined range
- product_id must be unique
- Only ADMIN can create/edit/delete
