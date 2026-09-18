# GrowthPilot AI — Task Checklist

## Phase 0 — Foundations ✅
- [x] Repository structure
- [x] SQLite + SQLAlchemy 2.x (no Docker)
- [x] All 24 SQLAlchemy models
- [x] FastAPI application entry point
- [x] Alembic migration config
- [x] Makefile (dev, seed, test, demo, reset-demo)
- [x] .env.example
- [x] Auth (Argon2, JWT httpOnly cookies, RBAC)
- [x] Health endpoint /health
- [x] Sandbox utilities

## Phase 1 — Data & Analytics ✅
- [x] Deterministic synthetic data generator (SEED=42)
- [x] Scenario manifest (planted scenarios)
- [x] Analytics engine (revenue, customers, inventory, payments)
- [x] Revenue change attribution decomposition
- [x] Inactive customers (own-cadence definition)
- [x] RFM segmentation
- [x] Churn model (logistic regression, time-split, no leakage)
- [x] Sales forecasting (baselines + Holt-Winters, backtest)
- [x] Opportunity engine (win-back, inventory, payment recovery, revenue decline)
- [x] Explainability payloads (WHAT/WHY/EVIDENCE/IMPACT/CONFIDENCE)

## Phase 2 — Action Core ✅
- [x] Policy Engine (L0–L4 risk tiers, kill switch, autonomy dial)
- [x] Action state machine (all states + illegal transition tests)
- [x] Idempotency key system
- [x] Approval gateway
- [x] Action executor (simulated, labeled)
- [x] Independent verifier
- [x] Hash-chained audit log writer + verify endpoint

## Phase 3 — API & Frontend ✅
- [x] FastAPI routers (auth, dashboard, opportunities, actions, audit, assistant, missions)
- [x] Next.js 15 frontend scaffold
- [x] Persistent SandboxBanner
- [x] Login page
- [x] Dashboard (KPIs, revenue chart, opportunities, actions)
- [x] Growth Opportunities page with ExplainPanel
- [x] AI Command Center (mission flow + step timeline)
- [x] Action Center (list + detail + approve/reject)
- [x] Audit Log timeline with chain verification
- [x] AI Assistant (intent detection, numeric grounding)
- [x] Inventory Intelligence page
- [x] Collections Recovery page
- [x] Customers page
- [x] Analytics page (revenue, attribution, retention)
- [x] Financial Readiness page (labeled "Demo eligibility")
- [x] Settings (autonomy dial, kill switch, quiet hours, reset demo)
- [x] Mobile bottom navigation
- [x] Dark/light mode support

## Phase 4 — Deployment ✅
- [x] Vercel deployment config (vercel.json)
- [x] Railway deployment config (railway.json + Procfile)
- [x] README with quickstart
- [x] TASKS.md (this file)
- [x] STATUS.md (honest status)
- [x] Removed Docker Compose (not needed)

## Remaining (P2 / Not built)
- [ ] Playwright E2E tests
- [ ] ML model training integration tests
- [ ] Voice input (Hindi/Hinglish)
- [ ] Real Paytm sandbox adapter
- [ ] Proof of Impact UI (control group measurement view)
- [ ] Advanced Thompson sampling / bandit optimization
- [ ] Multi-merchant switching UI
