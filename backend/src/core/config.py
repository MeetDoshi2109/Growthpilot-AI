"""
GrowthPilot Backend — Application Settings
SQLite (no Docker required), Gemini as default LLM provider.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────
    app_name: str = "GrowthPilot AI"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ── Database (SQLite — no Docker required) ────────────
    database_url: str = Field(default="sqlite+aiosqlite:///./growthpilot.db")
    sync_database_url: str = Field(default="sqlite:///./growthpilot.db")

    # ── Security / JWT ────────────────────────────────────
    jwt_secret_key: str = Field(default="growthpilot-dev-secret-change-in-prod-32c")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ── CORS ──────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Sandbox ───────────────────────────────────────────
    sandbox_mode: bool = True

    # ── Data Seeding ──────────────────────────────────────
    seed: int = 42
    num_customers: int = 5000
    num_transactions: int = 20000

    # ── LLM — Gemini default ──────────────────────────────
    llm_provider: Literal["mock", "none", "openai", "gemini"] = "gemini"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_max_tokens: int = 1024
    gemini_timeout_seconds: int = 30

    # OpenAI (fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 1024
    openai_timeout_seconds: int = 30

    llm_cost_log: bool = True
    llm_cache_ttl_seconds: int = 300

    # ── Business Rules ────────────────────────────────────
    contact_frequency_cap_days: int = 7
    control_group_fraction: float = 0.20
    rfm_window_days: int = 90
    churn_label_days: int = 30
    churn_training_window_days: int = 60
    inactive_cadence_multiplier: float = 2.0
    min_opportunity_confidence: float = 0.35
    default_autonomy_level: Literal["off", "recommend", "semi_auto", "full_auto"] = "recommend"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
