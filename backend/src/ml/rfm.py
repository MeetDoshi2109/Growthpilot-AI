"""
RFM Segmentation — deterministic quintile-based scoring.
Thresholds are documented here and in MODEL_CARDS.md.

Segments (per spec):
  Champions, Loyal, Potential Loyalists, At Risk,
  Can't Lose, New Customers, Dormant
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Any


@dataclass
class RFMResult:
    customer_id: str
    recency_days: int
    frequency: int
    monetary_paise: int
    r_score: int  # 1–5 (5=best)
    f_score: int
    m_score: int
    rfm_total: int
    segment: str


def compute_rfm(
    df: pd.DataFrame,  # columns: customer_id, recency_days, frequency, monetary_paise
    window_days: int = 90,
) -> list[RFMResult]:
    """
    Compute RFM scores for a DataFrame of customer metrics.
    Uses quintile scoring: 5 = best recency (most recent),
    5 = best frequency (most frequent), 5 = best monetary (highest spend).

    df must have: customer_id, recency_days (int), frequency (int), monetary_paise (int)
    """
    if df.empty:
        return []

    df = df.copy()

    # Recency: lower days = higher score
    df["r_score"] = pd.qcut(df["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    # Frequency: higher = better
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    # Monetary: higher = better
    df["m_score"] = pd.qcut(df["monetary_paise"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df["rfm_total"] = df["r_score"] + df["f_score"] + df["m_score"]

    results = []
    for _, row in df.iterrows():
        segment = _assign_segment(row["r_score"], row["f_score"], row["m_score"], row["rfm_total"])
        results.append(RFMResult(
            customer_id=str(row["customer_id"]),
            recency_days=int(row["recency_days"]),
            frequency=int(row["frequency"]),
            monetary_paise=int(row["monetary_paise"]),
            r_score=int(row["r_score"]),
            f_score=int(row["f_score"]),
            m_score=int(row["m_score"]),
            rfm_total=int(row["rfm_total"]),
            segment=segment,
        ))
    return results


def _assign_segment(r: int, f: int, m: int, total: int) -> str:
    """
    Deterministic rules — documented thresholds.

    Champions:        R≥4, F≥4, total≥11
    Loyal:            F≥4, total≥10
    Potential Loyal.: R≥3, F∈[2,3], total≥7
    At Risk:          R≤2, F≥3
    Can't Lose:       R≤2, F≥4
    New Customers:    R≥4, F==1
    Dormant:          R≤2, F≤2, total≤6
    """
    if r >= 4 and f >= 4 and total >= 11:
        return "champions"
    if r <= 2 and f >= 4:
        return "cant_lose"
    if r <= 2 and f >= 3:
        return "at_risk"
    if f >= 4 and total >= 10:
        return "loyal"
    if r >= 4 and f == 1:
        return "new_customers"
    if r >= 3 and f in (2, 3) and total >= 7:
        return "potential_loyalists"
    if r <= 2 and f <= 2 and total <= 6:
        return "dormant"
    # Default bucket
    if total >= 9:
        return "loyal"
    return "at_risk"


def segment_summary(results: list[RFMResult]) -> dict[str, Any]:
    """Aggregated counts and avg metrics per segment."""
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for r in results:
        buckets[r.segment].append(r)

    summary = {}
    for seg, items in buckets.items():
        summary[seg] = {
            "count": len(items),
            "avg_monetary_paise": int(np.mean([i.monetary_paise for i in items])),
            "avg_recency_days": round(np.mean([i.recency_days for i in items]), 1),
            "avg_frequency": round(np.mean([i.frequency for i in items]), 1),
        }
    return summary
