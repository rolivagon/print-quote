# Frontend: Fixed Products

## ADDED Requirements

### Requirement: Create Fixed Product Button
Administrators SHALL see a "Create as Product" button on the quote creation page.

#### Scenario: Admin sees button on quote page
Given an admin user is on the quote creation page
When the page loads
Then they see a "Crear como Producto" button

#### Scenario: Vendor does not see button
Given a vendor user is on the quote creation page
When the page loads
Then they do NOT see the "Create as Product" button

### Requirement: Create Fixed Product Modal
The system SHALL provide a modal for creating fixed products from quote configuration.

#### Scenario: Admin opens create product modal
Given an admin clicks "Create as Product"
When the modal opens
Then it shows:
  - Product ID input
  - Product name input
  - Client selector (optional)
  - Range table editor
  - Submit/Cancel buttons

#### Scenario: Admin fills and submits modal
Given the modal is open with valid data
When admin clicks "Create Product"
Then the API is called with quote data + ranges
And on success, a success message is shown

### Requirement: Fixed Products Management View
The system SHALL provide an admin view for managing fixed products.

#### Scenario: Admin navigates to fixed products
Given an admin is logged in
When they click "Productos Fijos" in the sidebar
Then they see a list of all fixed products

#### Scenario: Admin edits product ranges
Given admin is on fixed products list
When they click "Edit Ranges" on a product
Then they see the range editor
And can add/remove/modify ranges

### Requirement: Range Editor Component
The system SHALL provide a reusable component for managing quantity-price ranges.

#### Scenario: Add new range
Given the range editor is open
When admin adds range 11-20 at $25.000
And it doesn't overlap with existing ranges
Then the range is added to the table

#### Scenario: Validation prevents overlap
Given ranges 1-10 and 11-20 exist
When admin tries to add range 5-15
Then an error message is shown
And the range is not added

## MODIFIED Requirements

### Requirement: Update QuotesCreateView
The quote creation page SHALL be modified to include the "Create as Product" button and modal integration.

#### Scenario: Quote page includes product creation
Given the quote creation page
When it renders
Then it includes the "Create as Product" button (admin only)

## REMOVED Requirements

None

## UI Components

### Components to Create
- FixedProductRanges.vue - Range table editor
- CreateFixedProductModal.vue - Modal for creating products
- FixedProductsView.vue - Main management view

### Modified Components
- QuotesCreateView.vue - Add button and modal
- Sidebar.vue - Add menu item

### Routes
- /fixed-products - Fixed products list (admin only)
