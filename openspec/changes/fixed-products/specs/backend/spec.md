# Backend API: Fixed Products

## ADDED Requirements

### Requirement: Create Fixed Product from Quote
Administrators SHALL be able to create fixed products from existing quote configurations.

#### Scenario: Admin creates fixed product from digital quote
Given an admin user is on the quote creation page
And has filled in a complete quote configuration
When they click "Create as Product" button
And fill in product details (ID, name, ranges)
Then a fixed product is created with the quote snapshot
And the product is available for quoting

#### Scenario: Admin creates client-specific fixed product
Given an admin user is creating a fixed product
When they select a specific client
Then the product is only visible to that client

### Requirement: Quote using Fixed Product
Users SHALL be able to generate quotes using fixed products with predefined price ranges.

#### Scenario: Vendor quotes using fixed product within range
Given a fixed product "roller-80x200" exists
And it has range 1-3 at $38.500 per unit
When a vendor requests a quote for 2 units
Then the total is calculated as 2 × $38.500 = $77.000
And the applied range metadata is returned

#### Scenario: Quote quantity outside all ranges
Given a fixed product with ranges 1-10 and 11-100
When a vendor requests a quote for 150 units
Then an error is returned: "No price range found for quantity 150"

### Requirement: Manage Fixed Product Ranges
Administrators SHALL be able to manage price ranges for fixed products.

#### Scenario: Admin updates price ranges
Given a fixed product exists with existing ranges
When an admin updates the ranges via PATCH /ranges
And the new ranges don't overlap
Then the ranges are updated successfully

#### Scenario: Admin tries to create overlapping ranges
Given a fixed product exists
When an admin tries to add range 5-15
And range 1-10 already exists
Then an error is returned: "Ranges cannot overlap"

### Requirement: List and Filter Fixed Products
Users SHALL be able to list fixed products with various filters.

#### Scenario: List all global fixed products
Given multiple fixed products exist
When a user requests the list with include_globals=true
Then all global products are returned

#### Scenario: List products for specific client
Given products exist for client A and global products
When filtering by client_id=A
Then only products for client A plus globals are returned

## MODIFIED Requirements

None

## REMOVED Requirements

None

## Technical Specifications

### API Endpoints
- POST /api/v1/fixed-products/from-quote
- GET /api/v1/fixed-products
- GET /api/v1/fixed-products/{id}
- PATCH /api/v1/fixed-products/{id}/ranges
- DELETE /api/v1/fixed-products/{id}
- GET /api/v1/fixed-products/{id}/quote

### Data Models
- FixedProduct (id, product_id, name, print_type, client_id, base_quote_snapshot, is_active)
- FixedProductQuantityRange (id, fixed_product_id, min_quantity, max_quantity, unit_price)

### Database Schema
See design.md for complete schema
