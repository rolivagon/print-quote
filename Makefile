.PHONY: venv deps test cov fmt lint run all clean frontend-dev dev dev-bg dev-stop kill-ports \
        build-frontend serve tunnel tunnel-stop tunnel-quick supabase-start supabase-stop db-reset \
        test-unit test-supabase bootstrap-admin bootstrap-admin-local migrate-legacy load-digital-data load-plotter-data \
        load-plotter-data-prod

# Load local environment variables if .env.local exists
-include .env.local
export

# Default port for the API server
PORT ?= 8000
API_PORT ?= 5001
FRONTEND_PORT ?= 5173
SUPABASE_TEST_TARGETS ?= tests/integration tests/test_api
LOCAL_SUPABASE_FRONTEND_ENV = eval "$$(supabase status -o env)" && export VITE_SUPABASE_URL="$${VITE_SUPABASE_URL:-/supabase}" VITE_SUPABASE_PUBLISHABLE_KEY="$${VITE_SUPABASE_PUBLISHABLE_KEY:-$$ANON_KEY}"
LOCAL_SUPABASE_BACKEND_ENV = configured_supabase_url="$${SUPABASE_URL:-}" && eval "$$(supabase status -o env)" && export SUPABASE_URL="$${configured_supabase_url:-$$API_URL}"

# Create virtual environment
venv:
	python3.11 -m venv .venv
	.venv/bin/pip install -U pip

# Install dependencies
deps:
	.venv/bin/pip install -e .[dev]

# Run tests
test:
	.venv/bin/pytest -q --ignore=tests/test_api

# Pure pricing, domain, service, and token-validation tests; no database service is required.
test-unit:
	.venv/bin/pytest -q \
		tests/test_database_config.py tests/test_security.py tests/test_digital_steps.py \
		tests/test_offset_steps.py tests/test_plotter_steps.py tests/test_packing.py \
		tests/test_quote_service.py tests/test_fixed_products.py tests/test_domain

# Run tests with coverage
cov:
	.venv/bin/pytest --cov=src --cov-report=term-missing -q

# Format code
fmt:
	.venv/bin/ruff format

# Lint and fix code
lint:
	.venv/bin/ruff check --fix

# Run the API server with auto-reload (PORT defaults to 8000, override with: make run PORT=8080)
run:
	.venv/bin/uvicorn quote.api.main:app --reload --host 0.0.0.0 --port $(PORT)

# Run all: setup, format, lint, and test
all: venv deps fmt lint test

frontend-dev:
	@$(LOCAL_SUPABASE_FRONTEND_ENV) && cd frontend && npm run dev

# Kill the app's own dev servers (ports 5001, 5173, 5174) without relying on lsof.
# pkill matches the project's process cmdlines; the netstat fallback frees any
# orphaned reloader worker still bound to a target port (its cmdline only shows
# --multiprocessing-fork, which is too generic to match safely).
kill-ports:
	@echo "Cleaning up ports $(API_PORT), $(FRONTEND_PORT), 5174..."
	@pkill -9 -f "quote.api.main:app" 2>/dev/null || true
	@pkill -9 -f "frontend/node_modules/.bin/vite" 2>/dev/null || true
	@for port in $(API_PORT) $(FRONTEND_PORT) 5174; do \
		pids=$$(netstat -vanp tcp 2>/dev/null | awk -v port=".$$port" '$$4 ~ port"\$$" && $$6 == "LISTEN" {sub(/.*:/, "", $$11); print $$11}'); \
		if [ -n "$$pids" ]; then \
			echo "  Killing stragglers on port $$port: $$pids"; \
			kill -9 $$pids 2>/dev/null || true; \
		fi; \
	done
	@echo "Ports cleaned"

# Run both backend and frontend simultaneously
dev: kill-ports
	@echo "Starting backend on port $(API_PORT)..."
	@$(LOCAL_SUPABASE_BACKEND_ENV) && .venv/bin/uvicorn quote.api.main:app --reload --host 0.0.0.0 --port $(API_PORT) &
	@sleep 2
	@echo "Starting frontend (will try port $(FRONTEND_PORT) or next available)..."
	@$(LOCAL_SUPABASE_FRONTEND_ENV) && cd frontend && npm run dev &
	@sleep 3
	@echo ""
	@echo "✓ Servers started!"
	@echo "  Backend:  http://localhost:$(API_PORT)"
	@echo "  Frontend: http://localhost:$(FRONTEND_PORT) (or next available port)"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@wait

# Run both servers in background
dev-bg: kill-ports
	@echo "Starting backend on port $(API_PORT)..."
	@$(LOCAL_SUPABASE_BACKEND_ENV) && .venv/bin/uvicorn quote.api.main:app --reload --host 0.0.0.0 --port $(API_PORT) > /tmp/backend.log 2>&1 &
	@echo $$! > /tmp/backend.pid
	@sleep 2
	@echo "Starting frontend..."
	@$(LOCAL_SUPABASE_FRONTEND_ENV) && cd frontend && npm run dev > /tmp/frontend.log 2>&1 &
	@echo $$! > /tmp/frontend.pid
	@sleep 3
	@echo "✓ Both servers started in background!"
	@echo "  Backend:  http://localhost:$(API_PORT)"
	@echo "  Frontend: Check logs or try http://localhost:$(FRONTEND_PORT)"
	@echo ""
	@echo "Logs:"
	@echo "  tail -f /tmp/backend.log"
	@echo "  tail -f /tmp/frontend.log"
	@echo ""
	@echo "Stop with: make dev-stop"

# Stop background servers
dev-stop:
	@if [ -f /tmp/backend.pid ]; then kill $$(cat /tmp/backend.pid) 2>/dev/null || true; rm -f /tmp/backend.pid; echo "Backend stopped"; fi
	@if [ -f /tmp/frontend.pid ]; then kill $$(cat /tmp/frontend.pid) 2>/dev/null || true; rm -f /tmp/frontend.pid; echo "Frontend stopped"; fi
	@$(MAKE) kill-ports

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Start the local Supabase stack used by reset and integration checks.
supabase-start:
	@supabase start >/dev/null

supabase-stop:
	supabase stop

# Reset local Supabase from the checked-in Supabase migrations and seed configuration.
db-reset: supabase-start
	supabase db reset --local

# Run the tests that require local Supabase/PostgreSQL after rebuilding its schema.
test-supabase: db-reset
	RUN_SUPABASE_INTEGRATION=1 DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres \
	SUPABASE_URL=http://127.0.0.1:54321 \
	.venv/bin/pytest $(SUPABASE_TEST_TARGETS) -q

# Re-run Supabase integration tests without another database reset.
test-supabase-existing: supabase-start
	RUN_SUPABASE_INTEGRATION=1 DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres \
	SUPABASE_URL=http://127.0.0.1:54321 \
	.venv/bin/pytest $(SUPABASE_TEST_TARGETS) -q

# Create or reset the first administrator. Requires environment-only bootstrap credentials.
bootstrap-admin:
	.venv/bin/python scripts/bootstrap_admin.py

# Bootstrap against the running local Supabase stack without copying its service key to .env.local.
bootstrap-admin-local: supabase-start
	@eval "$$(supabase status -o env)" && export SUPABASE_URL="$${SUPABASE_URL:-$$API_URL}" SUPABASE_SERVICE_ROLE_KEY="$${SUPABASE_SERVICE_ROLE_KEY:-$$SERVICE_ROLE_KEY}" && .venv/bin/python scripts/bootstrap_admin.py

# Transition legacy users and their client/quote ownership with Supabase invitations.
migrate-legacy:
	.venv/bin/python scripts/migrate_legacy_users.py

# Add missing canonical digital catalog data without changing existing production rows.
load-digital-data:
	.venv/bin/python scripts/load_digital_data.py

# Add missing approved Plotter catalog data without changing existing rows.
load-plotter-data:
	.venv/bin/python scripts/load_plotter_data.py

# Load Plotter data with explicitly loaded production settings overriding .env.local.
load-plotter-data-prod:
	@set -a && . ./.env.prod && set +a && $(MAKE) -e load-plotter-data

# Build frontend for production
build-frontend:
	@echo "Building frontend for production..."
	@cd frontend && ./node_modules/.bin/vite build
	@echo "✓ Frontend built successfully!"

# Serve backend with frontend (production mode)
serve:
	@echo "Starting production server on port $(PORT)..."
	@echo "Frontend will be served from backend"
	@.venv/bin/uvicorn quote.api.main:app --host 0.0.0.0 --port $(PORT)

# Start Cloudflare tunnel
tunnel:
	@echo "Starting Cloudflare tunnel..."
	@echo "Your app will be available at a random *.trycloudflare.com URL"
	@cloudflared tunnel --url http://localhost:$(PORT)

# Stop Cloudflare tunnel (if running in background)
tunnel-stop:
	@pkill -f "cloudflared tunnel" 2>/dev/null || true
	@echo "✓ Cloudflare tunnel stopped"

# Quick tunnel: build frontend, start server and create tunnel in one command
tunnel-quick:
	@echo "Starting full tunnel setup..."
	@./scripts/start-tunnel.sh
