# ============================================================
# PAYTM GROWTHPILOT AI — Makefile
# No Docker required — uses SQLite + local Python/Node
# ============================================================

.PHONY: help dev dev-backend dev-frontend install install-backend install-frontend \
        seed seed-verify migrate migrate-generate test test-unit test-int \
        test-e2e test-evals test-security demo reset-demo lint format clean

PYTHON    := C:\Users\Asus\AppData\Local\Programs\Python\Python314\python.exe
PIP       := C:\Users\Asus\AppData\Local\Programs\Python\Python314\python.exe -m pip
NPM       := npm
BACKEND   := cd backend &&
FRONTEND  := cd frontend &&

# ── Default ───────────────────────────────────────────────
help:
	@echo ""
	@echo "  PAYTM GROWTHPILOT AI — Available Commands"
	@echo "  ==========================================="
	@echo "  No Docker required — uses SQLite + local Python/Node"
	@echo ""
	@echo "  Setup:"
	@echo "    make install          Install all dependencies (backend + frontend)"
	@echo "    make install-backend  Install Python dependencies"
	@echo "    make install-frontend Install Node.js dependencies"
	@echo ""
	@echo "  Development:"
	@echo "    make dev              Start backend + frontend dev servers"
	@echo "    make dev-backend      Start FastAPI backend only (port 8000)"
	@echo "    make dev-frontend     Start Next.js frontend only (port 3000)"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate          Run Alembic migrations (creates SQLite DB)"
	@echo "    make seed             Seed with deterministic synthetic data"
	@echo "    make seed-verify      Verify seeded scenarios match manifest"
	@echo ""
	@echo "  Testing:"
	@echo "    make test             Run all tests"
	@echo "    make test-unit        Unit tests (analytics, ML, opportunities)"
	@echo "    make test-int         Integration tests (action lifecycle)"
	@echo "    make test-e2e         Playwright end-to-end tests"
	@echo "    make test-evals       Evaluation harness"
	@echo "    make test-security    Security tests (tenant isolation, injection)"
	@echo ""
	@echo "  Demo:"
	@echo "    make demo             Full demo: migrate + seed + start servers"
	@echo "    make reset-demo       Delete DB, re-seed, restart servers"
	@echo ""

# ── Install ───────────────────────────────────────────────
install: install-backend install-frontend
	@echo "✅ All dependencies installed."

install-backend:
	@echo "🐍 Installing Python dependencies..."
	$(BACKEND) $(PIP) install -e ".[dev]"

install-frontend:
	@echo "📦 Installing Node.js dependencies..."
	$(FRONTEND) $(NPM) install
	@echo "🎨 Installing design quality tools..."
	-$(FRONTEND) npx skills add Leonxlnx/taste-skill 2>/dev/null || true
	-$(FRONTEND) npx impeccable install 2>/dev/null || true

# ── Development Servers ───────────────────────────────────
dev:
	@echo "🚀 Starting GrowthPilot (backend + frontend)..."
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API Docs: http://localhost:8000/docs"
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	@echo "🐍 Starting FastAPI backend on :8000..."
	$(BACKEND) uvicorn src.main:app --reload --port 8000 --host 0.0.0.0

dev-frontend:
	@echo "⚛️  Starting Next.js frontend on :3000..."
	$(FRONTEND) $(NPM) run dev

# ── Database ──────────────────────────────────────────────
migrate:
	@echo "🗄️  Running Alembic migrations (SQLite)..."
	$(BACKEND) alembic upgrade head
	@echo "✅ Database ready at backend/growthpilot.db"

migrate-generate:
	@echo "🗄️  Generating new Alembic migration..."
	$(BACKEND) alembic revision --autogenerate -m "$(msg)"

migrate-rollback:
	@echo "⏪ Rolling back last migration..."
	$(BACKEND) alembic downgrade -1

# ── Seeding ───────────────────────────────────────────────
seed:
	@echo "🌱 Seeding database with deterministic synthetic data (SEED=42)..."
	$(BACKEND) $(PYTHON) -m scripts.seed
	@echo ""
	@echo "  ✅ Seed complete!"
	@echo "  📊 Hero merchant: Rajesh Tea & Snacks"
	@echo "  👤 Login: rajesh@teaandsnacks.com / demo1234"
	@echo ""

seed-verify:
	@echo "🔍 Verifying seeded scenarios against scenario_manifest.json..."
	$(BACKEND) $(PYTHON) -m scripts.verify_seed

# ── Testing ───────────────────────────────────────────────
test: test-unit test-int
	@echo "✅ All tests passed."

test-unit:
	@echo "🧪 Running unit tests..."
	$(BACKEND) $(PYTHON) -m pytest tests/unit -v --tb=short

test-int:
	@echo "🧪 Running integration tests..."
	$(BACKEND) $(PYTHON) -m pytest tests/integration -v --tb=short

test-e2e:
	@echo "🧪 Running Playwright E2E tests..."
	$(FRONTEND) npx playwright test

test-evals:
	@echo "📊 Running evaluation harness..."
	$(BACKEND) $(PYTHON) -m pytest tests/evals -v --tb=short

test-security:
	@echo "🔒 Running security tests..."
	$(BACKEND) $(PYTHON) -m pytest tests/security -v --tb=short

# ── Demo (one-command) ────────────────────────────────────
demo: migrate seed
	@echo ""
	@echo "  ╔══════════════════════════════════════════════╗"
	@echo "  ║   PAYTM GROWTHPILOT AI — DEMO               ║"
	@echo "  ║   Sandbox · Synthetic Demo Data              ║"
	@echo "  ╚══════════════════════════════════════════════╝"
	@echo ""
	@echo "  Starting servers..."
	@$(MAKE) -j2 dev-backend dev-frontend

reset-demo:
	@echo "🔄 Resetting demo — deleting database and re-seeding..."
	-rm -f backend/growthpilot.db
	@$(MAKE) migrate
	@$(MAKE) seed
	@echo "✅ Demo reset complete. Fresh state ready."
	@$(MAKE) -j2 dev-backend dev-frontend

# ── Linting & Formatting ──────────────────────────────────
lint:
	@echo "🔍 Linting backend (ruff + mypy)..."
	$(BACKEND) ruff check src tests
	$(BACKEND) mypy src --ignore-missing-imports
	@echo "🔍 Linting frontend (eslint)..."
	$(FRONTEND) $(NPM) run lint

format:
	@echo "🎨 Formatting backend (black + ruff)..."
	$(BACKEND) black src tests
	$(BACKEND) ruff check --fix src tests
	@echo "🎨 Formatting frontend (prettier)..."
	$(FRONTEND) $(NPM) run format

# ── Cleanup ───────────────────────────────────────────────
clean:
	@echo "🧹 Cleaning generated artifacts..."
	-find backend -type d -name __pycache__ -exec rm -rf {} +
	-find backend -type f -name "*.pyc" -delete
	-find backend -type d -name .pytest_cache -exec rm -rf {} +
	-find backend -type d -name .mypy_cache -exec rm -rf {} +
	-cd frontend && rm -rf .next out
	@echo "✅ Clean complete."

clean-db:
	@echo "⚠️  Deleting SQLite database..."
	-rm -f backend/growthpilot.db
	@echo "✅ Database deleted. Run 'make migrate && make seed' to recreate."
