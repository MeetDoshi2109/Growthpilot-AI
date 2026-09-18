# GrowthPilot AI — Assumptions

*Updated: Phase 1 build*

| # | Assumption | Rationale |
|---|---|---|
| 1 | LLM provider defaults to `MockLLM` | Crash-proof demo; no API key required. Real providers plug in via env var. |
| 2 | PostgreSQL via Docker Compose | Production-correct; matches spec. Can be swapped for SQLite for local-only. |
| 3 | Money stored as integer paise | Avoids float precision bugs. ₹100 = 10000 paise. All UI divides by 100. |
| 4 | Seed is always `SEED=42` | Reproducible demo. Changing seed changes scenarios but not schema. |
| 5 | Hero merchant is "Rajesh Tea & Snacks" | One well-engineered merchant surfaces all demo scenarios cleanly. |
| 6 | "Inactive customer" = no purchase in > 2× their own median cadence | Customer-relative definition, not a fixed 30-day window. |
| 7 | Win-back campaign uses conservative prior (10% response rate) when history is thin | Avoids over-optimistic projections; confidence is lowered and labeled. |
| 8 | Churn label = no purchase in the next 30 days among customers active in prior 60 | Documented in MODEL_CARDS.md. Time-split train/val, no leakage. |
| 9 | Financial Readiness is clearly labeled "Demo eligibility" — not a real loan application | Compliance and trust requirement. |
| 10 | Payment links use `sandbox.growthpilot.local` domain | Clearly fake; prevents confusion with real UPI flows. |
| 11 | IST (Asia/Kolkata, UTC+5:30) for all UI timestamps | Indian merchant context. |
| 12 | No Paytm logo assets used without explicit permission | Using generic "GrowthPilot" brand with Paytm-inspired color palette. |
| 13 | Voice input (P2) implemented via Web Speech API | No external STT service required for demo. |
| 14 | `LLM_PROVIDER=none` produces template-based explanations for all opportunities | Ensures demo works even if LLM quota is exhausted. |
| 15 | Contact frequency cap = 1 campaign per customer per 7 days | Prevents spam; enforced at opportunity deduplication layer. |
| 16 | Impact measurement uses 20% control group split | Standard A/B; randomization at customer_id hash. |
| 17 | Autonomy dial default = "Recommend" (human approves all actions) | Most conservative default; merchant can increase autonomy in settings. |
| 18 | All prices in INR; no multi-currency support | Paytm India context only. |
| 19 | RFM quintiles computed on rolling 90-day window | Balances recency with sufficient data for stable scores. |
| 20 | Forecasting baseline is seasonal naive; model only deployed if it beats baseline on MAPE | Avoids degrading to a worse forecast in sparse-data scenarios. |
