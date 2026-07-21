# Design: Fixed Products

## Architecture

### Backend Layer Structure
```
src/quote/
├── domain/
│   └── models.py          # FixedProduct, QuantityRange (Pydantic)
├── repo/
│   ├── models/
│   │   └── fixed_product.py  # SQLModel entities
│   ├── interfaces.py      # FixedProductRepository ABC
│   └── sql_fixed_product_repo.py  # SQL implementation
├── service/
│   └── quote_service.py   # create_fixed_product_from_quote(), quote_with_fixed_product()
└── api/
    ├── schemas.py         # FixedProduct schemas
    └── fixed_products.py  # Router with endpoints
```

### Database Schema
```sql
-- fixed_products
CREATE TABLE fixed_products (
    id UUID PRIMARY KEY,
    product_id VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    print_type VARCHAR NOT NULL,
    client_id UUID REFERENCES clients(id),
    base_quote_snapshot JSON NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- fixed_product_quantity_ranges
CREATE TABLE fixed_product_quantity_ranges (
    id UUID PRIMARY KEY,
    fixed_product_id UUID REFERENCES fixed_products(id) ON DELETE CASCADE,
    min_quantity INTEGER NOT NULL,
    max_quantity INTEGER NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(fixed_product_id, min_quantity, max_quantity)
);

CREATE INDEX idx_fixed_products_client ON fixed_products(client_id);
CREATE INDEX idx_fixed_products_type ON fixed_products(print_type);
```

### Snapshot JSON Structure
```json
{
  "reference_quantity": 100,
  "dimensions": {"width_cm": 80.0, "height_cm": 200.0},
  "paper_id": 5,
  "paper_name": "Sintético 300g",
  "color_mode": "4/0",
  "finishes": [{"id": 1, "name": "Corte Recto"}],
  "sheet_config": {...},
  "geometry": {...},
  "pieces_per_sheet": 2,
  "sheets_needed": 50,
  "calculated_costs": {...}
}
```

## Frontend Design

### Two-Phase Flow

#### Phase 1: Create Product (from Quote)
- Admin fills quote form and calculates price
- Clicks "Crear como Producto" button
- Modal opens with:
  - Product ID input
  - Name input
  - Client selector (optional, null by default)
- Submit creates product WITHOUT ranges
- Success message shown, modal closes

#### Phase 2: Manage Ranges (Detail View)
- Admin navigates to Fixed Products list
- Clicks on a product → goes to detail view
- Detail view shows:
  - Product info (name, type, snapshot preview)
  - Range management table (initially empty)
  - "Agregar Rango" button
- Similar to PaperPricing management

### QuotesCreateView.vue Changes
```vue
<!-- Add button next to "Crear Cotización" -->
<button v-if="isAdmin" @click="showCreateProductModal = true">
  <BoxIcon /> Crear como Producto
</button>

<!-- Modal - Simple, no ranges -->
<CreateFixedProductModal
  v-model="showCreateProductModal"
  :quote-data="currentQuoteData"
  @created="onProductCreated"
/>
```

### FixedProductsView.vue (List)
Structure similar to PapersView.vue:
- Table listing: name, type, range count, actions
- Filters: print type, search by name
- Actions: view detail, delete
- NO edit ranges action (moved to detail)

### FixedProductDetailView.vue (Detail)
Similar to Paper detail with pricing:
- Product information card
- Base quote snapshot preview (read-only)
- Range management section:
  - Table with min_qty, max_qty, unit_price
  - Add/Edit/Delete range buttons
  - Overlap validation messages

### Component Hierarchy
```
FixedProductsView.vue (List)
├── FixedProductList.vue
│   └── FixedProductTable.vue
│       └── FixedProductRow.vue
│           └── ViewDetailButton → FixedProductDetailView.vue

FixedProductDetailView.vue (Detail)
├── ProductInfoCard.vue
├── RangeManagementSection.vue
│   └── RangeTable.vue
│       └── RangeRow.vue
│           └── Edit/Delete actions
│   └── AddRangeButton → AddRangeModal.vue
```

## Security
- Role-based access: ADMIN only for CRUD
- Vendedores: read-only access to list and quote endpoints
- Client-specific products only visible to that client + admins

## Performance Considerations
- Index on (client_id, print_type, is_active)
- Cache product list if > 100 products
- Pagination on listing endpoint
