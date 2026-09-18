# PAYTM GROWTHPILOT AI

> **"Your AI business partner that finds opportunities, makes decisions, takes action, and proves the result."**

[![Sandbox](https://img.shields.io/badge/Sandbox-Synthetic%20Demo%20Data-amber)](.)
[![Independent hackathon prototype](https://img.shields.io/badge/Type-Hackathon%20Prototype-blue)](.)

---

## What is GrowthPilot?

GrowthPilot is an AI operating system for Paytm merchants. It observes transaction data, understands patterns, identifies opportunities, recommends actions, executes them (with your approval), verifies results, and measures impact — all in one coherent loop.

**Core loop:**
`OBSERVE → UNDERSTAND → IDENTIFY → RECOMMEND → APPROVE → EXECUTE → VERIFY → MEASURE → LEARN`

**Three tracks in one product:**
- 🚀 **Track 1 — Merchant Growth AI:** Win-back campaigns, inventory alerts, payment recovery
- 💰 **Track 2 — Financial Readiness:** Explainable cash-flow profile (demo eligibility only)
- 🤖 **Track 3 — Autonomous AI Teammates:** Mission engine with live task timeline

---

## Quickstart (Local, No Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### 1. Backend
```bash
cd backend
pip install -e ".[dev]"

# Start the API server
uvicorn src.main:app --reload --port 8000

# In another terminal, seed the database
python -m scripts.seed
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

**Login:** `rajesh@teaandsnacks.com` / `demo1234`

### Or use the Makefile
```bash
# From project root
make install    # install all deps
make dev        # start both servers
make seed       # seed the database
make demo       # migrate + seed + start
make reset-demo # wipe DB, re-seed, restart
```

---

## Vercel Deployment

### Frontend → Vercel
1. Push the repository to GitHub
2. Connect to [Vercel](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Set environment variable: `NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL`
5. Deploy

### Backend → Railway
1. Connect your GitHub repo to [Railway](https://railway.app)
2. Set **Root Directory** to `backend`
3. Set environment variables (see `.env.example`)
4. Railway auto-detects `railway.json` and starts the app

---

## Architecture

```
Merchant (browser)
    ↓ HTTPS
Next.js 15 (Vercel)
    ↓ API calls
FastAPI (Railway/Render)
    ↓
Policy Engine → Action Executor → Verifier
    ↓
Hash-chained Audit Log
    ↓
SQLite (file-based, seeded with synthetic data)
```

---

## Key Features

| Feature | Status |
|---|---|
| Dashboard with real computed KPIs | ✅ Implemented |
| AI Command Center (mission flow) | ✅ Implemented |
| Growth Opportunities with explainability | ✅ Implemented |
| Win-back campaign (full lifecycle) | ✅ Implemented |
| Policy Engine (L0–L4 risk tiers) | ✅ Implemented |
| Hash-chained Audit Trail | ✅ Implemented |
| Action lifecycle state machine | ✅ Implemented |
| Inventory Intelligence | ✅ Implemented |
| Collections Recovery | ✅ Implemented |
| Financial Readiness (demo eligibility) | ✅ Implemented (labeled) |
| AI Assistant (numeric grounding) | ✅ Implemented |
| Proof of Impact (control groups) | 🔶 Backend ready, UI partial |
| Voice (Hindi/Hinglish) | ❌ P2 — not built |
| Real Paytm API integration | ❌ P2 — mock adapter only |

---

## Trust & Safety

- **Persistent Sandbox badge** on every page
- **Numbers from data, not AI** — all ₹ amounts computed by analytics engine
- **LLM never mutates state** — only proposes; policy + tools execute
- **Every action:** validate → policy → approval → execute → verify → audit
- **Kill switch** and **autonomy dial** in Settings
- **Tenant isolation** enforced in repository layer
- **PII masked** in audit logs and LLM prompts
- **Financial Readiness labeled** "Demo eligibility — not a credit decision"

---

## Honest Limitations

- SQLite is used for portability; swap `DATABASE_URL` for PostgreSQL in production
- ML models (churn, forecast) trained on synthetic data — not validated on real merchant data
- LLM integration uses mock templates by default; set `LLM_PROVIDER=gemini` with API key for natural language
- Voice input not implemented (P2)
- No real Paytm APIs connected

---

## Sandbox Disclosure

This is an **independent hackathon prototype**. It uses **100% synthetic, seeded data**.
No real Paytm data, real merchant data, real money movement, real SMS/WhatsApp messages,
or real loan applications are used or implied.

All simulated actions are labeled `simulated: true` in API responses and marked "Simulated" in the UI.
