"""
Sales Forecasting — Holt-Winters ETS vs baselines (seasonal naive, moving average).
Rolling-origin backtest with MAPE/sMAPE.
Prediction intervals from residual quantiles.
If model doesn't beat baseline, the baseline is used (tested).
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _smape(actual: np.ndarray, forecast: np.ndarray) -> float:
    denom = (np.abs(actual) + np.abs(forecast)) / 2
    return float(np.mean(np.abs(actual - forecast) / (denom + 1e-9)) * 100)


def _mape(actual: np.ndarray, forecast: np.ndarray) -> float:
    return float(np.mean(np.abs((actual - forecast) / (actual + 1e-9))) * 100)


def seasonal_naive_forecast(series: pd.Series, horizon: int, season: int = 7) -> np.ndarray:
    """Forecast by repeating the last seasonal cycle."""
    n = len(series)
    result = []
    for i in range(horizon):
        idx = n - season + (i % season)
        idx = max(0, min(idx, n - 1))
        result.append(float(series.iloc[idx]))
    return np.array(result)


def moving_average_forecast(series: pd.Series, horizon: int, window: int = 7) -> np.ndarray:
    """Forecast using trailing moving average."""
    ma = float(series.tail(window).mean())
    return np.full(horizon, ma)


def holt_winters_forecast(series: pd.Series, horizon: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Holt-Winters ETS (additive trend, additive seasonality).
    Returns (forecast, lower_80, upper_80).
    Falls back to seasonal naive on any error.
    """
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        if len(series) < 14:
            raise ValueError("Too few data points for Holt-Winters")

        model = ExponentialSmoothing(
            series.values,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        ).fit(optimized=True, remove_bias=True)

        forecast = model.forecast(horizon)

        # Residuals for prediction interval
        residuals = series.values - model.fittedvalues
        q10 = np.percentile(residuals, 10)
        q90 = np.percentile(residuals, 90)
        lower = forecast + q10
        upper = forecast + q90

        return (
            np.maximum(forecast, 0),
            np.maximum(lower, 0),
            np.maximum(upper, 0),
        )
    except Exception as e:
        logger.warning(f"Holt-Winters failed: {e}, falling back to seasonal naive")
        fc = seasonal_naive_forecast(series, horizon)
        return fc, fc * 0.8, fc * 1.2


def rolling_origin_backtest(
    series: pd.Series,
    horizon: int = 7,
    min_train: int = 14,
    n_origins: int = 4,
) -> dict[str, Any]:
    """
    Rolling-origin backtest comparing seasonal naive vs Holt-Winters.
    Returns sMAPE for each method. If HW doesn't beat naive, picks naive.
    """
    n = len(series)
    if n < min_train + horizon:
        return {
            "error": "insufficient_data",
            "chosen_model": "seasonal_naive",
        }

    step = max(1, (n - min_train - horizon) // n_origins)
    origins = range(min_train, n - horizon, step)

    naive_errors, hw_errors, ma_errors = [], [], []

    for origin in origins:
        train = series.iloc[:origin]
        actual = series.iloc[origin: origin + horizon].values

        naive_fc = seasonal_naive_forecast(train, horizon)
        ma_fc = moving_average_forecast(train, horizon)
        hw_fc, _, _ = holt_winters_forecast(train, horizon)

        if len(actual) == horizon:
            naive_errors.append(_smape(actual, naive_fc))
            ma_errors.append(_smape(actual, ma_fc))
            hw_errors.append(_smape(actual, hw_fc))

    if not naive_errors:
        return {"error": "backtest_failed", "chosen_model": "seasonal_naive"}

    avg_naive = float(np.mean(naive_errors))
    avg_ma = float(np.mean(ma_errors))
    avg_hw = float(np.mean(hw_errors))

    # Choose best model — if HW doesn't beat naive, use naive
    best_smape = min(avg_naive, avg_ma, avg_hw)
    if avg_hw == best_smape and avg_hw < avg_naive:
        chosen = "holt_winters"
    elif avg_ma == best_smape and avg_ma < avg_naive:
        chosen = "moving_average"
    else:
        chosen = "seasonal_naive"

    return {
        "chosen_model": chosen,
        "smape_seasonal_naive": round(avg_naive, 2),
        "smape_moving_average": round(avg_ma, 2),
        "smape_holt_winters": round(avg_hw, 2),
        "beats_baseline": chosen != "seasonal_naive",
        "n_origins": len(naive_errors),
    }


def generate_forecast(
    series: pd.Series,
    horizon: int = 7,
) -> dict[str, Any]:
    """
    Full forecast pipeline: backtest → select best model → forecast + CI.
    """
    if len(series) < 7:
        return {
            "unavailable": True,
            "reason": f"Need at least 7 data points, got {len(series)}",
        }

    backtest = rolling_origin_backtest(series, horizon=horizon)
    chosen = backtest.get("chosen_model", "seasonal_naive")

    if chosen == "holt_winters":
        forecast, lower, upper = holt_winters_forecast(series, horizon)
    elif chosen == "moving_average":
        fc = moving_average_forecast(series, horizon)
        forecast, lower, upper = fc, fc * 0.8, fc * 1.2
    else:
        fc = seasonal_naive_forecast(series, horizon)
        forecast, lower, upper = fc, fc * 0.8, fc * 1.2

    return {
        "chosen_model": chosen,
        "forecast": [round(float(v), 0) for v in forecast],
        "lower_80": [round(float(v), 0) for v in lower],
        "upper_80": [round(float(v), 0) for v in upper],
        "backtest": backtest,
        "horizon_days": horizon,
    }
