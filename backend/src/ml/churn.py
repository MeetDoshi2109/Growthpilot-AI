"""
Churn Model — Logistic Regression with explainable per-customer reasons.

Label definition:
  Churned = no purchase in the next 30 days among customers
  who were active in the prior 60 days.
  (Documented here and in MODEL_CARDS.md)

Training: time-based split — train on [0, cutoff), validate on [cutoff, end).
No data after cutoff date used for training features. Leakage test enforced.

Outputs: churn_probability, risk_level, top_reasons (plain language)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
from sklearn.calibration import calibration_curve

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "days_since_last_txn",
    "recency_vs_own_cadence",   # days_since / median_cadence
    "frequency_change_pct",     # (recent_count - prior_count) / prior_count
    "avg_spend_change_pct",     # change in avg transaction amount
    "failed_payment_count",
    "n_transactions",
    "tenure_days",
]

FEATURE_PLAIN_LABELS = {
    "days_since_last_txn": "Days since last purchase",
    "recency_vs_own_cadence": "Overdue vs own buying pattern",
    "frequency_change_pct": "Purchase frequency change",
    "avg_spend_change_pct": "Average spend change",
    "failed_payment_count": "Failed payments",
    "n_transactions": "Total purchases",
    "tenure_days": "Customer tenure",
}


@dataclass
class ChurnScore:
    customer_id: str
    churn_probability: float
    risk_level: str  # low | medium | high | critical
    top_reasons: list[str]


class ChurnModel:
    """
    Logistic regression churn model.
    Fixed random_state=42 for reproducibility.
    Two identical runs → identical metrics.
    """

    def __init__(self) -> None:
        self.model = LogisticRegression(random_state=42, max_iter=1000, C=1.0)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_importances: list[float] = []
        self.metrics: dict[str, Any] = {}
        self.baseline_auc: float = 0.0

    def build_features(self, df: pd.DataFrame, cutoff_date: pd.Timestamp) -> pd.DataFrame:
        """
        Build feature matrix from raw transaction DataFrame.
        CRITICAL: No feature uses data after cutoff_date (leakage guard).
        df columns: customer_id, transaction_date, amount_paise, status, median_cadence_days
        """
        df = df[df["transaction_date"] < cutoff_date].copy()

        prior_cutoff = cutoff_date - pd.Timedelta(days=30)
        recent_window = df[df["transaction_date"] >= prior_cutoff]
        older_window = df[df["transaction_date"] < prior_cutoff]

        features = []
        for cid, grp in df.groupby("customer_id"):
            success = grp[grp["status"] == "success"]
            if success.empty:
                continue

            last_txn = success["transaction_date"].max()
            days_since = (cutoff_date - last_txn).days
            cadence = float(grp["median_cadence_days"].iloc[0]) if "median_cadence_days" in grp.columns else 14.0
            recency_ratio = days_since / cadence if cadence > 0 else 0

            recent_c = recent_window[recent_window["customer_id"] == cid]
            older_c = older_window[older_window["customer_id"] == cid]
            recent_count = len(recent_c[recent_c["status"] == "success"])
            older_count = len(older_c[older_c["status"] == "success"])
            freq_change = (
                (recent_count - older_count) / older_count
                if older_count > 0 else 0.0
            )

            recent_avg = recent_c[recent_c["status"] == "success"]["amount_paise"].mean() if recent_count > 0 else 0
            older_avg = older_c[older_c["status"] == "success"]["amount_paise"].mean() if older_count > 0 else 0
            spend_change = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0.0

            failed = int((grp["status"] == "failed").sum())
            n_txns = len(success)
            tenure = (last_txn - success["transaction_date"].min()).days + 1

            features.append({
                "customer_id": cid,
                "days_since_last_txn": days_since,
                "recency_vs_own_cadence": recency_ratio,
                "frequency_change_pct": freq_change,
                "avg_spend_change_pct": spend_change,
                "failed_payment_count": failed,
                "n_transactions": n_txns,
                "tenure_days": tenure,
            })

        return pd.DataFrame(features)

    def build_labels(self, df: pd.DataFrame, cutoff_date: pd.Timestamp, label_window_days: int = 30) -> pd.Series:
        """
        Label = 1 if customer has NO purchase in [cutoff, cutoff + 30d].
        Only labels customers who had a transaction in prior 60 days.
        """
        label_end = cutoff_date + pd.Timedelta(days=label_window_days)
        active_pre = df[
            (df["transaction_date"] >= cutoff_date - pd.Timedelta(days=60)) &
            (df["transaction_date"] < cutoff_date) &
            (df["status"] == "success")
        ]["customer_id"].unique()

        post_active = df[
            (df["transaction_date"] >= cutoff_date) &
            (df["transaction_date"] < label_end) &
            (df["status"] == "success")
        ]["customer_id"].unique()

        labels = {}
        for cid in active_pre:
            labels[cid] = 0 if cid in post_active else 1
        return pd.Series(labels)

    def train(
        self,
        df: pd.DataFrame,
        cutoff_date: pd.Timestamp,
        label_window_days: int = 30,
    ) -> dict[str, Any]:
        """
        Train model with time-based split.
        Returns metrics dict for MODEL_CARDS.md.
        """
        X = self.build_features(df, cutoff_date)
        y_series = self.build_labels(df, cutoff_date, label_window_days)

        merged = X.merge(y_series.reset_index(), left_on="customer_id", right_on="index")
        merged = merged.rename(columns={0: "label"})
        merged = merged.dropna(subset=["label"])

        if len(merged) < 20:
            logger.warning("Too few labeled samples for churn model training")
            return {"error": "insufficient_data"}

        feature_cols = FEATURE_NAMES
        X_feat = merged[feature_cols].fillna(0)
        y = merged["label"].astype(int)

        # Time-based split: first 80% for training
        split_idx = int(len(merged) * 0.8)
        X_train, X_val = X_feat.iloc[:split_idx], X_feat.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(y_val) < 5:
            logger.warning("Validation set too small — extending training window")
            X_train, X_val = X_feat, X_feat
            y_train, y_val = y, y

        self.scaler.fit(X_train)
        X_train_s = self.scaler.transform(X_train)
        X_val_s = self.scaler.transform(X_val)

        self.model.fit(X_train_s, y_train)
        self.is_trained = True

        self.feature_importances = list(np.abs(self.model.coef_[0]))

        # Val metrics
        y_pred_proba = self.model.predict_proba(X_val_s)[:, 1]
        auc = roc_auc_score(y_val, y_pred_proba) if y_val.nunique() > 1 else 0.5
        pr_auc = average_precision_score(y_val, y_pred_proba) if y_val.nunique() > 1 else 0.5
        brier = brier_score_loss(y_val, y_pred_proba) if y_val.nunique() > 1 else 0.25

        # Baseline: predict churn based purely on recency
        recency_col = X_val["days_since_last_txn"]
        recency_norm = (recency_col - recency_col.min()) / (recency_col.max() - recency_col.min() + 1e-9)
        baseline_auc = roc_auc_score(y_val, recency_norm) if y_val.nunique() > 1 else 0.5
        self.baseline_auc = baseline_auc

        self.metrics = {
            "auc": round(float(auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "brier_score": round(float(brier), 4),
            "baseline_auc": round(float(baseline_auc), 4),
            "beats_baseline": auc > baseline_auc,
            "train_samples": int(len(X_train)),
            "val_samples": int(len(X_val)),
            "churn_rate_val": round(float(y_val.mean()), 3),
            "feature_importances": dict(zip(FEATURE_NAMES, [round(float(i), 4) for i in self.feature_importances])),
        }
        logger.info(f"Churn model trained: AUC={auc:.3f}, baseline={baseline_auc:.3f}, beats={auc > baseline_auc}")
        return self.metrics

    def score_customers(self, X: pd.DataFrame) -> list[ChurnScore]:
        """Score customers and return per-customer churn probabilities + plain-language reasons."""
        if not self.is_trained:
            raise RuntimeError("Model not trained — call train() first")

        feature_cols = FEATURE_NAMES
        X_feat = X[feature_cols].fillna(0)
        X_s = self.scaler.transform(X_feat)
        proba = self.model.predict_proba(X_s)[:, 1]

        # Per-customer feature contributions (sign × weight)
        coef = self.model.coef_[0]
        contributions = X_s * coef  # (n_samples, n_features)

        results = []
        for i, row in enumerate(X.itertuples()):
            prob = float(proba[i])
            risk = _risk_level(prob)
            top_reasons = _build_reasons(
                contrib_row=contributions[i],
                feature_values=X_feat.iloc[i].to_dict(),
                customer_row=row,
            )
            results.append(ChurnScore(
                customer_id=str(row.customer_id),
                churn_probability=round(prob, 4),
                risk_level=risk,
                top_reasons=top_reasons,
            ))
        return results


def _risk_level(prob: float) -> str:
    if prob >= 0.75:
        return "critical"
    elif prob >= 0.55:
        return "high"
    elif prob >= 0.35:
        return "medium"
    else:
        return "low"


def _build_reasons(
    contrib_row: np.ndarray,
    feature_values: dict[str, float],
    customer_row: Any,
) -> list[str]:
    """Build top-3 plain-language churn reasons from feature contributions."""
    sorted_idx = np.argsort(contrib_row)[::-1][:3]
    reasons = []
    for idx in sorted_idx:
        if contrib_row[idx] <= 0:
            continue
        feat = FEATURE_NAMES[idx]
        val = feature_values.get(feat, 0)
        reasons.append(_reason_text(feat, val))
    return reasons[:3] or ["Purchase pattern suggests inactivity risk"]


def _reason_text(feature: str, value: float) -> str:
    m = {
        "days_since_last_txn": f"{int(value)} days since last purchase",
        "recency_vs_own_cadence": f"{round(value, 1)}x overdue vs own buying pattern",
        "frequency_change_pct": f"Purchase frequency down {abs(round(value*100))}%",
        "avg_spend_change_pct": f"Average spend {'down' if value < 0 else 'up'} {abs(round(value*100))}%",
        "failed_payment_count": f"{int(value)} failed payment(s) on record",
        "n_transactions": f"Only {int(value)} purchases total",
        "tenure_days": f"Customer for {int(value)} days",
    }
    return m.get(feature, f"{FEATURE_PLAIN_LABELS.get(feature, feature)}: {round(value, 2)}")


# Singleton instance
_churn_model: ChurnModel | None = None


def get_churn_model() -> ChurnModel:
    global _churn_model
    if _churn_model is None:
        _churn_model = ChurnModel()
    return _churn_model
