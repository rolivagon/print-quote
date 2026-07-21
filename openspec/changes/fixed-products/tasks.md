# Tasks: Fixed Products Implementation

## Phase 1: Backend - Models & Repository [TDD]

### Task 1.1: Create Domain Models
**File:** `src/quote/domain/models.py`
- [ ] Add FixedProduct Pydantic model
- [ ] Add QuantityRange Pydantic model
- [ ] Add validation: ranges cannot overlap

**Test:** `tests/test_domain/test_fixed_product.py`
```python
def test_fixed_product_creation():
def test_quantity_range_validation():
def test_overlapping_ranges_raises_error():
```

### Task 1.2: Create SQL Models
**File:** `src/quote/repo/models/fixed_product.py`
- [ ] Create FixedProduct SQLModel entity
- [ ] Create FixedProductQuantityRange SQLModel entity
- [ ] Add relationships and constraints

### Task 1.3: Create Repository Interface
**File:** `src/quote/repo/interfaces.py`
- [ ] Add FixedProductRepository ABC
- [ ] Methods: create, get_by_id, list, update_ranges, delete

### Task 1.4: Implement SQL Repository
**File:** `src/quote/repo/sql_fixed_product_repo.py`
- [ ] Implement FixedProductRepository
- [ ] Add range overlap validation
- [ ] Add transaction handling

**Test:** `tests/test_repo/test_fixed_product_repo.py`
```python
def test_create_fixed_product():
def test_list_fixed_products():
def test_get_by_id():
def test_update_ranges():
def test_range_overlap_validation():
```

### Task 1.5: Create Alembic Migration
```bash
.venv/bin/alembic revision --autogenerate -m "add fixed products"
```
- [ ] Review generated migration
- [ ] Apply: `alembic upgrade head`

---

## Phase 2: Backend - API [TDD]

### Task 2.1: Create API Schemas
**File:** `src/quote/api/schemas.py`
- [ ] FixedProductCreate schema
- [ ] FixedProductResponse schema
- [ ] FixedProductRange schema
- [ ] FixedProductQuoteResponse schema

### Task 2.2: Create API Router
**File:** `src/quote/api/fixed_products.py`
- [ ] POST /from-quote (create without ranges)
- [ ] GET / (list)
- [ ] GET /{id} (detail with ranges)
- [ ] POST /{id}/ranges (add new range)
- [ ] PUT /{id}/ranges/{range_id} (update range)
- [ ] DELETE /{id}/ranges/{range_id} (delete range)
- [ ] DELETE /{id} (delete product)
- [ ] GET /{id}/quote?quantity={n} (quote with product)

### Task 2.3: Integrate with QuoteService
**File:** `src/quote/service/quote_service.py`
- [ ] create_fixed_product_from_quote() method
- [ ] quote_with_fixed_product() method
- [ ] list_fixed_products() method

**Test:** `tests/test_service/test_fixed_products.py`
```python
def test_create_fixed_product_from_quote():
def test_quote_with_fixed_product_range_1_to_3():
def test_quote_with_fixed_product_outside_range():
```

### Task 2.4: API Integration Tests
**File:** `tests/test_api/test_fixed_products_api.py`
```python
def test_api_create_fixed_product_from_quote_without_ranges():
def test_api_list_fixed_products():
def test_api_add_range_to_product():
def test_api_update_range():
def test_api_delete_range():
def test_api_quote_with_fixed_product():
def test_api_delete_fixed_product():
```

---

## Phase 3: Frontend - Components [TDD]

### Task 3.1: Create FixedProductRanges Component
**File:** `frontend/src/components/fixed-products/FixedProductRanges.vue`
- [ ] Range table with add/edit/delete
- [ ] Overlap validation UI
- [ ] Save changes functionality

### Task 3.2: Create CreateFixedProduct Modal
**File:** `frontend/src/components/fixed-products/CreateFixedProductModal.vue`
- [ ] Product ID input
- [ ] Name input
- [ ] Client selector (optional, default null)
- [ ] Submit to API (creates product without ranges)
- [ ] Success message and close modal
- [ ] Note: Ranges are added later in detail view

### Task 3.3: Update QuotesCreateView
**File:** `frontend/src/views/Quotes/QuotesCreateView.vue`
- [ ] Add "Crear como Producto" button (admin only)
- [ ] Integrate CreateFixedProductModal
- [ ] Pass current quote data to modal

---

## Phase 4: Frontend - Views

### Task 4.1: Create FixedProductsView (List)
**File:** `frontend/src/views/FixedProducts/FixedProductsView.vue`
- [ ] List table with filters
- [ ] View detail action → navigates to detail
- [ ] Delete action with confirmation
- [ ] NO range editing here (moved to detail)

### Task 4.2: Create FixedProductDetailView (Detail)
**File:** `frontend/src/views/FixedProducts/FixedProductDetailView.vue`
- [ ] Product info card (read-only snapshot preview)
- [ ] Range management section
- [ ] Add/Edit/Delete range functionality
- [ ] Overlap validation
- [ ] Similar to Paper pricing management

### Task 4.3: Add Routes
**File:** `frontend/src/router/index.ts`
- [ ] Add /fixed-products route (list)
- [ ] Add /fixed-products/:id route (detail)
- [ ] Add admin guard to both routes

### Task 4.4: Update Sidebar
**File:** `frontend/src/components/layout/Sidebar.vue`
- [ ] Add "Productos Fijos" menu item (admin only)
- [ ] Icon: BoxIcon or similar

---

## Phase 5: Integration & QA

### Task 5.1: End-to-End Testing

#### Flow 1: Create Product from Quote
- [ ] Admin fills quote form and calculates
- [ ] Admin clicks "Crear como Producto"
- [ ] Admin fills product ID and name (no ranges)
- [ ] Product created successfully

#### Flow 2: Manage Ranges
- [ ] Admin navigates to Fixed Products list
- [ ] Admin clicks on product to view detail
- [ ] Admin adds range 1-10 at $1000
- [ ] Admin adds range 11-20 at $900
- [ ] Validation prevents adding overlapping range 5-15

#### Flow 3: Quote Using Fixed Product
- [ ] Vendedor selects fixed product
- [ ] Enters quantity 5
- [ ] Gets price $5000 (5 × $1000)
- [ ] Enters quantity 25
- [ ] Gets error "No range found for quantity 25"

### Task 5.2: Code Quality
```bash
make fmt
make lint
make test
make cov
```

### Task 5.3: Documentation
- [ ] Update API docs
- [ ] Update user guide
- [ ] Add feature to changelog

---

## Acceptance Criteria Checklist

### Phase 1: Product Creation
- [ ] Admin can create fixed product from quote page (without ranges)
- [ ] Product is created with client_id=null by default
- [ ] Product has snapshot of base quote configuration

### Phase 2: Range Management
- [ ] Admin can view fixed products list
- [ ] Admin can navigate to product detail
- [ ] Admin can add ranges in detail view
- [ ] Admin can edit ranges in detail view
- [ ] Admin can delete ranges in detail view
- [ ] Ranges cannot overlap (validation)

### Phase 3: Quoting
- [ ] Vendedor can quote using fixed product
- [ ] Price calculation uses range unit_price (not base calculation)
- [ ] Error shown if quantity outside all ranges

### Quality
- [ ] All tests pass
- [ ] Code formatted and linted
- [ ] API docs updated
