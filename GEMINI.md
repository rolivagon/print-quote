# Print Quote Project Context

## Project Overview

`print-quote` is a Python 3.11 application designed to calculate print quotes. It supports various printing methodologies including Digital, Offset, and Plotter, along with packing services. The project relies on a clean, layered architecture separating business logic, pricing strategies, and data access.

**Key Technologies:**
-   **Language:** Python 3.11+
-   **Validation:** `pydantic>=2`
-   **Testing:** `pytest`, `pytest-cov`
-   **Linting/Formatting:** `ruff`

## Architecture

The codebase is organized into four distinct layers within `src/quote/`:

1.  **Domain Layer** (`src/quote/domain/`):
    -   Contains core business entities and value objects.
    -   Key files: `models.py` (Pydantic models for Quote, Product, Customer) and `enums.py`.
2.  **Pricing Layer** (`src/quote/pricing/`):
    -   Implements the Strategy pattern for different pricing mechanisms.
    -   Includes specific strategies for `digital.py`, `offset.py`, `plotter.py`, and `packing.py`.
    -   `money.py` handles currency and value operations.
3.  **Repository Layer** (`src/quote/repo/`):
    -   Abstracts data access.
    -   Currently provides an in-memory implementation (`inmem.py`) suitable for testing and development.
4.  **Service Layer** (`src/quote/service/`):
    -   `quote_service.py` acts as the main entry point for business logic, orchestrating interactions between the domain, pricing, and repository layers.

## Building and Running

The project uses a `Makefile` to streamline common development tasks. Ensure you have Python 3.11 installed.

### Setup
1.  **Create Virtual Environment:**
    ```bash
    make venv
    ```
    *Note: The virtual environment is created in `.venv`.*

2.  **Install Dependencies:**
    ```bash
    make deps
    ```
    *Note: This installs both runtime and development dependencies (pytest, ruff).*

### Testing
-   **Run Unit Tests:**
    ```bash
    make test
    ```
-   **Run Tests with Coverage:**
    ```bash
    make cov
    ```
-   **Manual Test Execution:**
    ```bash
    .venv/bin/pytest tests/test_specific_file.py -v
    ```

### Code Quality
-   **Format Code:**
    ```bash
    make fmt
    ```
-   **Lint and Fix:**
    ```bash
    make lint
    ```

### Full Development Cycle
To run the entire pipeline (setup, format, lint, and test):
```bash
make all
```

## Development Conventions

-   **Code Style:**
    -   Adhere to `ruff` configuration defined in `pyproject.toml`.
    -   Line length: 100 characters.
    -   Quotes: Double quotes.
    -   Indentation: Spaces.
-   **Testing:**
    -   All new logic must be accompanied by unit tests in the `tests/` directory.
    -   Use `pytest` fixtures found in `tests/conftest.py`.
-   **Imports:**
    -   Follow standard Python import sorting (handled by `ruff`).
-   **Virtual Environment:**
    -   Always work within the `.venv` virtual environment. The `Makefile` commands explicitly call binaries from `.venv/bin/`.
