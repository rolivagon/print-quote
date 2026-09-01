# PRS: Costos internos de producción en cotizaciones

## Status

In Review

## Purpose

Permitir que la imprenta configure costos internos de producción independientes de los precios de venta actuales y que los administradores visualicen, al cotizar, cuánto cuesta producir cada ítem. El desglose debe calcular papel, impresión y terminaciones cuando exista información suficiente, conservar separados los costos offset de planchas y tiraje, y comunicar explícitamente los componentes sin configuración sin impedir la generación de la cotización.

## Requirements

- REQ-001: The system shall preserve the existing paper, finish, and plotter catalog prices as selling prices and shall store internal production costs separately.
- REQ-002: When an administrator creates or edits a paper, the system shall allow optional internal paper and printing costs for Digital and Offset using the `sheet` unit and for Plotter using the `sqm` unit.
- REQ-003: When an administrator creates or edits a finish, the system shall allow optional internal costs by print type (`digital`, `plotter`, or `offset`) and cost unit, initially including `sheet` and reserving `job`, `sqm`, `per_item`, and `per_1000` for future configuration.
- REQ-004: When a Digital quote has an internal paper or printing cost configured in `sheet`, the system shall calculate that component using the sheets consumed by the item, including the applicable waste defined by the existing Digital calculation.
- REQ-005: When an Offset quote has an internal paper or printing cost configured in `sheet`, the system shall calculate that component using the sheets consumed with waste by the item.
- REQ-006: When a Plotter quote has an internal paper or printing cost configured in `sqm`, the system shall calculate that component using the billable square meters already defined by the Plotter pricing rules.
- REQ-007: When a quote includes a finish with an internal cost configured for the quote print type and a compatible calculation unit, the system shall calculate and include the finish cost using the quantity represented by that unit.
- REQ-008: If a quote includes a finish whose required internal cost is missing or whose configured unit is incompatible with the quote calculation, then the system shall report that component as `no indicado` and shall exclude it from the internal cost total.
- REQ-009: If a paper or printing internal cost is missing for a quote item, then the system shall calculate all available internal components, report the missing component, and shall not block quote creation.
- REQ-010: When an Offset quote is calculated, the system shall keep plate, run, and other existing Offset-specific costs separate from internal paper and printing costs.
- REQ-011: When the system calculates a quote, the system shall expose to administrators a breakdown containing internal paper cost, internal printing cost, internal finishing cost, existing separate Offset-specific costs, internal cost total, and missing-cost notices.
- REQ-012: When the system returns a quote to a seller or another non-administrative role, the system shall not expose the internal production cost breakdown or its component values.
- REQ-013: When the system persists a quote with internal costs, the system shall store a snapshot of the configured costs and calculation results used for that quote so later catalog edits do not alter the historical breakdown.
- REQ-014: When an internal cost is absent, the system shall represent it as unknown or not indicated rather than as a zero-valued cost in the administrative breakdown.
- REQ-015: Where internal cost values are monetary, the system shall validate non-negative values and calculate them using `Decimal` with the application's configured currency precision.

## Tasks

- [x] T-001: Add failing domain and pricing tests proving the internal cost units and missing-cost result model required by REQ-003, REQ-008, REQ-009, REQ-014, and REQ-015.
- [x] T-002: Add failing persistence and migration tests for technology-specific paper and finish internal costs, optional values, compatible units, and historical quote snapshots required by REQ-001, REQ-002, REQ-003, and REQ-013; add the Supabase migration and SQLModel persistence.
- [x] T-003: Add failing API tests for administrator create/update forms and role-filtered quote responses required by REQ-002, REQ-003, REQ-011, and REQ-012; implement schemas, repositories, routers, and response composition without exposing internal costs to non-administrators.
- [x] T-004: Add failing Digital, Offset, and Plotter pricing tests for sheet waste, Offset sheets with waste, Plotter billable square meters, and separated Offset-specific costs required by REQ-004, REQ-005, REQ-006, and REQ-010; implement the calculations in `src/quote/pricing/` rather than in API routes.
- [x] T-005: Add failing API tests for partial calculations and missing-cost notices required by REQ-008, REQ-009, and REQ-014; integrate the pricing result into quote persistence and administrator responses.
- [x] T-006: Add failing frontend tests or the repository's established equivalent for editing paper and finish internal costs and rendering the administrator-only breakdown required by REQ-002, REQ-003, REQ-011, and REQ-012; implement the forms and shared quote breakdown without duplicating a separate preview view.
- [x] T-007: Run formatting, linting, backend tests, Supabase migration/integration tests, and the frontend lint/build checks; record the results before moving the PRS to review.

## Acceptance Checks

- [x] Existing selling-price catalogs remain unchanged and are distinguishable from internal production costs in API responses, persistence, and administration forms.
- [x] Administrators can optionally configure Digital/Offset paper and printing costs per `sheet`, Plotter paper and printing costs per `sqm`, and finish costs by print type with the initially supported `sheet` unit.
- [x] Digital and Offset internal paper/printing costs use consumed sheets including their existing waste rules; Plotter uses billable `sqm`.
- [x] A Plotter finish configured only with `sheet` cost is shown as `no indicado` and contributes nothing to the internal total until a compatible `sqm` cost exists.
- [x] Missing paper, printing, or finishing costs do not prevent quote creation; the administrator response identifies each missing component and sums only available components.
- [x] Offset plate, run, and other Offset-specific costs remain separate from paper and printing internal costs.
- [x] The administrator quote response contains the internal breakdown, total, and notices, while non-administrative responses contain no internal cost values.
- [x] A persisted quote retains the internal cost snapshot used at creation, including configured rates, units, print type, finish IDs, metrics, statuses, and results.
- [x] Invalid negative monetary values are rejected and all monetary calculations use `Decimal`; configured zero values remain distinct from missing values.
- [x] The relevant checks pass in the documented order: `make fmt`, `make lint`, `make test`, and the required Supabase and frontend checks.

## Verification Notes

- `make fmt`, `make lint`, and `make test` pass (`239 passed, 24 skipped`).
- `npm test -- --run` passes (`11 passed`), and `npm run lint`, `npm run format`, and `npm run build` pass; the build reports existing CSS/chunk-size warnings.
- `make test-supabase-existing` passes (`135 passed, 1 xfailed`) after applying the migration; the internal-cost API integration tests cover CRUD, rollback validation, admin-only access, Digital sheets, Offset waste, Plotter billable sqm, missing costs, zero values, and snapshots, including real authenticated admin/seller HTTP access.
- `make test-supabase` passes (`135 passed, 1 xfailed`) after resetting and applying the migration.
- The HTTP admin test covers POST and PATCH attempts for future finish units (`sqm`, `job`, `per_item`, `per_1000`), verifies 422 responses, and confirms no attempted finish or cost rows are persisted.
- Future finish units (`sqm`, `job`, `per_item`, `per_1000`) are rejected with 422 and are not offered or persisted; `InternalCostManager` initializes finishes with `sheet` for Digital, Offset, and Plotter.
- `InternalCostManager` now resets on target changes and ignores stale load/save responses; lifecycle request-version coverage passes in the frontend test suite.
- The PRS is now `In Review`; it must not be moved to `Done` by the implementer.

## Constraints

- Pricing logic belongs in `src/quote/pricing/`; API routers compose pricing and persistence but do not own pricing rules.
- Persistent SQLModel entities belong in `src/quote/repo/models/`, and public schema changes are made only through checked-in migrations under `supabase/migrations/`; Alembic is not used.
- All monetary values use `Decimal`; runtime persistence requires PostgreSQL/Supabase and has no SQLite fallback.
- The existing selling prices are not reused or copied as internal costs because they represent customer-facing prices and no reliable historical internal-cost source exists.
- Internal costs are optional. Missing values must remain distinguishable from configured zero values and must not be silently converted to zero.
- A Plotter finish cost is compatible only when its internal unit matches the Plotter calculation unit; no implicit conversion from `sheet` to `sqm` is introduced.
- Plate, run, and other Offset-specific costs remain separate unless a later approved requirement changes that behavior.
- Backend authorization is authoritative; frontend visibility alone is insufficient to protect internal costs.
- Existing views and components should be extended or shared rather than duplicated, and any repeated calculation or response mapping should be extracted only when it is a clear reusable unit.
- Implementation starts only after this PRS receives explicit approval. The PRS must be critically reviewed before it can be marked `Done`.
