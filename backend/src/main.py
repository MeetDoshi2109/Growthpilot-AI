"""
GrowthPilot AI -- FastAPI Application Entry Point
Sandbox - Synthetic Demo Data
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import create_all_tables

logger = structlog.get_logger()

SANDBOX_LABEL = "Sandbox - Synthetic Demo Data"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info(
        "GrowthPilot AI starting",
        environment=settings.environment,
        sandbox=settings.sandbox_mode,
    )
    await create_all_tables()
    logger.info("Database tables ready (SQLite)")
    yield
    logger.info("GrowthPilot AI shutting down")


app = FastAPI(
    title="GrowthPilot AI API",
    description=(
        "Paytm GrowthPilot AI - Your AI business partner that finds opportunities, "
        "makes decisions, takes action, and proves the result. "
        "Sandbox - Synthetic Demo Data - No real Paytm data or money movement."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── System endpoints ──────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "sandbox": settings.sandbox_mode,
        "sandbox_label": SANDBOX_LABEL,
        "simulated": True,
    }


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "app": settings.app_name,
        "tagline": "Your AI business partner that finds opportunities, makes decisions, takes action, and proves the result.",
        "docs": "/docs",
        "health": "/health",
        "sandbox_label": SANDBOX_LABEL,
        "simulated": True,
    }


# ── API Routers ───────────────────────────────────────────────────────────────
from src.api.v1 import router as v1_router  # noqa: E402
app.include_router(v1_router, prefix="/api/v1")
