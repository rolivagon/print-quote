# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`print-quote` is a Python 3.11 project for calculating print quotes with support for different printing types (digital, offset, plotter) and packing services. The project follows a layered architecture with clear separation of concerns.

## Development Commands

### Environment Setup
- `make venv` - Create Python 3.11 virtual environment in `.venv`
- `make deps` - Install dependencies from pyproject.toml

### Development Workflow
- `make test` - Run pytest tests (quick mode)
- `make cov` - Run tests with coverage report
- `make fmt` - Format code with ruff
- `make lint` - Lint and auto-fix code issues
- `make all` - Complete development cycle (venv + deps + fmt + lint + test)

### Testing
- Uses pytest as test framework
- Test files located in `tests/` directory
- Run single test: `.venv/bin/pytest tests/test_specific.py -v`
- Coverage reports: `make cov`

## Architecture

### Layered Structure
- **Domain Layer** (`src/quote/domain/`): Core business models and enums
  - `models.py`: Pydantic models (Quote, Product, Customer)
  - `enums.py`: Business enums (PrintType, PackingType)

- **Pricing Layer** (`src/quote/pricing/`): Strategy pattern for pricing calculations
  - `base.py`: Abstract PricingStrategy interface
  - `digital.py`, `offset.py`, `plotter.py`: Print-specific strategies
  - `packing.py`: Packing pricing strategy
  - `money.py`: Money value object with currency support

- **Repository Layer** (`src/quote/repo/`): Data access abstraction
  - `interfaces.py`: Repository interfaces
  - `inmem.py`: In-memory implementation for testing

- **Service Layer** (`src/quote/service/`): Business logic orchestration
  - `quote_service.py`: Main service for quote operations

### Key Dependencies
- `pydantic>=2` for data validation and serialization
- `pytest` and `pytest-cov` for testing
- `ruff` for linting and formatting

### Code Style
- Line length: 100 characters
- Uses ruff for formatting and linting
- Target Python 3.11+