# GrowthPilot AI — Architecture

## System Overview

PAYTM GROWTHPILOT AI is a full-stack, AI-powered merchant intelligence platform built for the Paytm AI Hackathon. It functions as an AI operating system for Paytm merchants — observing data, understanding patterns, identifying opportunities, recommending actions, executing them (with approval), verifying results, measuring impact, and learning.

## Core Loop

```
OBSERVE → UNDERSTAND → IDENTIFY OPPORTUNITY → RECOMMEND → APPROVE
    → EXECUTE → VERIFY → MEASURE IMPACT → LEARN
```

## Architecture Diagram

```
Merchant (text / voice)
   ↓
Conversation / Command Center
   ↓
Intent Detection (rules + LLM fallback classifier, schema-validated)
   ↓
Agent Orchestrator (state machine)
   ↓
Specialized Agent (controlled tool allowlist)
   ↓
Typed Tool Call (Pydantic-validated)
   ↓
Policy Engine (validate, limits, ownership, dedupe, risk tier)
   ↓
Approval Gateway (if required by autonomy settings)
   ↓
Action Executor (idempotent, transactional, idempotency keys)
   ↓
Verifier (independent re-read of state)
   ↓
Audit Log (append-only, hash-chained)
   ↓
Impact Tracker (control group) → Learning Loop
   ↓
Response (numbers injected from tool results, not LLM-generated)
```

## Layering Rule

```
analytics/ML (deterministic)
    → opportunity engine
        → agents/tools
            → policy
                → execution
                    → verification
                        → audit
```

**The LLM sits only at:**
1. Intent parsing
2. Plan drafting (within strict schema)
3. Natural-language explanation

Each LLM output is Pydantic-validated with a deterministic fallback. The system operates fully with `LLM_PROVIDER=none`.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript (strict), Tailwind CSS, shadcn/ui, Recharts, Framer Motion, TanStack Query, Zod |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x async, Alembic |
| Database | PostgreSQL 16 (integer paise for money, UTC timestamps) |
| ML/Analytics | pandas, numpy, scikit-learn, statsmodels |
| Auth | Argon2 password hashing, JWT httpOnly Secure SameSite cookies |
| LLM | LLMProvider interface: MockLLM / OpenAI / Gemini / None |
| DevEx | Docker Compose, Makefile, pre-commit, GitHub Actions |

## Repository Structure

```
/
├── frontend/           # Next.js 15 App Router
│   ├── app/            # Pages and layouts
│   ├── components/     # Reusable UI components
│   ├── features/       # Feature-specific components
│   ├── lib/            # API client, formatting, hooks
│   ├── hooks/          # Custom React hooks
│   └── types/          # TypeScript type definitions
├── backend/
│   └── src/
│       ├── api/v1/     # FastAPI routers
│       ├── models/     # SQLAlchemy models
│       ├── schemas/    # Pydantic schemas
│       ├── repositories/ # Tenant-scoped data access
│       ├── analytics/  # Deterministic analytics engine
│       ├── ml/         # ML models (churn, segmentation, forecasting)
│       ├── opportunities/ # Opportunity engine
│       ├── agents/     # Specialized agents with tool allowlists
│       ├── orchestrator/ # Mission state machine
│       ├── tools/      # Typed, Pydantic-validated tools
│       ├── policies/   # Policy engine + approval gateway
│       ├── execution/  # Executor, verifier, audit writer
│       ├── adapters/   # PaytmAdapter interface + MockPaytmAdapter
│       ├── ai/         # LLM provider, guardrails, verifier
│       └── core/       # Config, security, database, logging
├── data/
│   ├── generators/     # Deterministic synthetic data generator
│   ├── seeds/          # SQL seed files
│   └── golden/         # Golden datasets for unit tests
├── docs/               # Architecture, assumptions, status, tasks
├── scripts/            # Seed, reset-demo, eval, benchmark
└── tests/
    ├── unit/           # Analytics, ML, opportunity engine
    ├── integration/    # Action lifecycle, tenant isolation
    ├── e2e/            # Playwright tests
    ├── evals/          # Numeric grounding, opportunity recovery
    └── security/       # Prompt injection, tenant isolation
```

## Trust Principles

1. **Numbers from code, not LLM** — all ₹ amounts, counts, dates from analytics engine
2. **LLM never mutates state** — only proposes; policy engine + typed tools execute
3. **Every action passes:** validate → policy → (approval) → execute → verify → audit
4. **Idempotent and reversible** — idempotency keys; compensation/rollback on failure
5. **Honest simulation** — persistent "Sandbox · Demo Data" badge; `simulated: true` in all API responses
6. **Works with no LLM** — `LLM_PROVIDER=none` produces template-based explanations

## Agents and Tool Allowlists

| Agent | Tools |
|---|---|
| Merchant Intelligence | analyze_sales, get_kpis |
| Growth | calculate_growth_opportunities |
| Customer | get_customer_segments, get_customer |
| Sales | analyze_sales, forecast_sales |
| Inventory | get_inventory, create_restock_order |
| Collections | find_overdue_payments, send_payment_reminder, create_payment_link, schedule_followup |
| Financial Readiness | get_financial_profile, simulate_application |
| Campaign | create_campaign, send_campaign, create_customer_offer |

## Data Conventions

- **Money:** integer paise (₹100 = 10000 paise), `currency='INR'`
- **Timestamps:** stored UTC, displayed in Asia/Kolkata (IST)
- **Formatting:** `Intl.NumberFormat('en-IN')` for Indian lakh/crore grouping
- **Tenant isolation:** every row has `merchant_id`, repositories enforce scoping
- **Sandbox:** all simulated actions have `simulated=true` in API responses

## Sandbox Mode

Every deployment of this project operates in Sandbox mode with synthetic data:
- Persistent header badge: **"Sandbox · Synthetic Demo Data"**
- Payment links use `sandbox.growthpilot.local/pay/...` format
- All external actions (SMS, UPI, loans) are simulated — labeled in UI + audit log
- No real Paytm data, real messages sent, or real money movement
