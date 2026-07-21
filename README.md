# Print Quote

A Python project for print quote calculations with support for different printing types (digital, offset, plotter) and packing services.

## Setup

### Prerequisites

- Python 3.11

### Installation

1. Create and activate virtual environment:
   ```bash
   python3.11 -m venv .venv && source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   make deps
   ```

3. Run tests to verify setup:
   ```bash
   make test
   ```

## Development

### Available Make Commands

- `make venv` - Create virtual environment
- `make deps` - Install dependencies
- `make test` - Run tests
- `make cov` - Run tests with coverage
- `make fmt` - Format code with ruff
- `make lint` - Lint and fix code issues
- `make all` - Complete setup and validation (venv, deps, format, lint, test)
- `make clean` - Clean build artifacts

### Project Structure

```
src/quote/
├── domain/          # Business models and enums
├── pricing/         # Pricing strategies for different print types
├── repo/           # Data access layer
└── service/        # Business logic orchestration

tests/              # Test files
```

## Architecture

The project follows a layered architecture:

- **Domain Layer**: Core business models (`Quote`, `Product`, `Customer`) and enums (`PrintType`, `PackingType`)
- **Pricing Layer**: Strategy pattern implementation for different pricing calculations
- **Repository Layer**: Data access abstraction with in-memory implementation
- **Service Layer**: Business logic orchestration and use case implementations