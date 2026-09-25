"""Outcome-driven feedback learning for the trading agent.

The feedback model is deliberately separate from the primary market model. It
learns from the agent's own resolved signal outcomes and can calibrate future
probabilities without changing execution or risk controls.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss

from src.learning.store import SignalOutcome, SignalOutcomeStore


class FeedbackLearner:
    """Learn a conservative probability calibration layer from past signals."""

    def __init__(
        self,
        store: SignalOutcomeStore,
        *,
        min_samples: int = 40,
        blend_weight: float = 0.25,
        random_state: int = 42,
    ) -> None:
        if min_samples < 10:
            raise ValueError("min_samples must be at least 10")
        if not 0.0 <= blend_weight <= 1.0:
            raise ValueError("blend_weight must be between 0 and 1")
        self.store = store
        self.min_samples = min_samples
        self.blend_weight = blend_weight
        self.random_state = random_state
        self.calibrator: LogisticRegression | None = None
        self.metrics: dict[str, float] = {}

    @staticmethod
    def _utc_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    def record_prediction(
        self,
        *,
        signal_id: str,
        symbol: str,
        direction: int,
        probability: float,
        entry_price: float,
        signal_time: pd.Timestamp,
        horizon_bars: int,
        model_version: str,
        user_id: str = "agent",
    ) -> None:
        """Record a prediction before its future outcome is known."""
        if direction not in (-1, 1):
            raise ValueError("learning predictions must have direction -1 or 1")
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if horizon_bars <= 0:
            raise ValueError("horizon_bars must be positive")

        self.store.append(
            SignalOutcome(
                signal_id=signal_id,
                user_id=user_id,
                symbol=symbol,
                direction="long" if direction > 0 else "short",
                probability=probability,
                entry_price=entry_price,
                signal_time=self._utc_timestamp(signal_time).isoformat(),
                horizon_bars=horizon_bars,
                model_version=model_version,
            )
        )

    def resolve_pending(self, symbol: str, market_data: pd.DataFrame) -> int:
        """Resolve signals only after their full forward horizon is observable."""
        if "Close" not in market_data.columns or market_data.empty:
            return 0

        index = pd.DatetimeIndex(market_data.index)
        if index.tz is None:
            index = index.tz_localize("UTC")
        else:
            index = index.tz_convert("UTC")

        resolved = 0
        for record in self.store.latest():
            if record.symbol != symbol or record.exit_price is not None:
                continue
            if not record.signal_time or record.horizon_bars <= 0:
                continue

            signal_time = self._utc_timestamp(record.signal_time)
            signal_position = int(index.searchsorted(signal_time, side="left"))
            target_position = signal_position + record.horizon_bars
            if signal_position >= len(index) or target_position >= len(index):
                continue

            entry_price = float(record.entry_price)
            exit_price = float(market_data["Close"].iloc[target_position])
            if exit_price <= 0:
                continue

            raw_return = exit_price / entry_price - 1.0
            realized_return = raw_return if record.direction == "long" else -raw_return
            outcome = "win" if realized_return > 0 else "loss" if realized_return < 0 else "flat"

            updated = replace(
                record,
                exit_price=exit_price,
                realized_return=float(realized_return),
                outcome=outcome,
            )
            self.store.append(updated)
            resolved += 1

        return resolved

    def fit(self) -> dict[str, float]:
        """Fit a time-ordered calibrator and promote it only if it helps."""
        records = [
            record
            for record in self.store.latest()
            if record.exit_price is not None
            and record.realized_return is not None
            and record.outcome in {"win", "loss"}
        ]
        records.sort(key=lambda item: item.signal_time)

        if len(records) < self.min_samples:
            self.calibrator = None
            self.metrics = {"samples": float(len(records)), "active": 0.0}
            return self.metrics

        probabilities = np.asarray([record.probability for record in records], dtype=float)
        labels = np.asarray([1 if record.outcome == "win" else 0 for record in records], dtype=int)
        if len(np.unique(labels)) < 2:
            self.calibrator = None
            self.metrics = {"samples": float(len(records)), "active": 0.0}
            return self.metrics

        split = max(int(len(records) * 0.7), 1)
        if split >= len(records):
            self.calibrator = None
            self.metrics = {"samples": float(len(records)), "active": 0.0}
            return self.metrics

        X_train = probabilities[:split].reshape(-1, 1)
        y_train = labels[:split]
        X_test = probabilities[split:].reshape(-1, 1)
        y_test = labels[split:]

        if len(np.unique(y_train)) < 2 or len(y_test) == 0:
            self.calibrator = None
            self.metrics = {"samples": float(len(records)), "active": 0.0}
            return self.metrics

        candidate = LogisticRegression(random_state=self.random_state, max_iter=1000)
        candidate.fit(X_train, y_train)
        calibrated = candidate.predict_proba(X_test)[:, 1]
        raw_test = probabilities[split:]

        raw_brier = float(brier_score_loss(y_test, raw_test))
        candidate_brier = float(brier_score_loss(y_test, calibrated))
        raw_accuracy = float(accuracy_score(y_test, raw_test >= 0.5))
        candidate_accuracy = float(accuracy_score(y_test, calibrated >= 0.5))

        if candidate_brier <= raw_brier and candidate_accuracy >= raw_accuracy - 0.02:
            self.calibrator = candidate
            self.metrics = {
                "samples": float(len(records)),
                "active": 1.0,
                "raw_brier": raw_brier,
                "calibrated_brier": candidate_brier,
                "raw_accuracy": raw_accuracy,
                "calibrated_accuracy": candidate_accuracy,
            }
        else:
            self.calibrator = None
            self.metrics = {
                "samples": float(len(records)),
                "active": 0.0,
                "raw_brier": raw_brier,
                "calibrated_brier": candidate_brier,
                "raw_accuracy": raw_accuracy,
                "calibrated_accuracy": candidate_accuracy,
            }
        return self.metrics

    def adjust_probability(self, probability: float) -> float:
        """Apply the learned calibration conservatively, when promoted."""
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if self.calibrator is None:
            return probability
        calibrated = float(self.calibrator.predict_proba([[probability]])[0, 1])
        return float(
            np.clip(
                probability * (1.0 - self.blend_weight) + calibrated * self.blend_weight,
                0.0,
                1.0,
            )
        )

    def save(self, path: str | Path) -> None:
        """Persist the promoted calibrator and its validation metrics."""
        if self.calibrator is None:
            return
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "calibrator": self.calibrator,
                "metrics": self.metrics,
                "blend_weight": self.blend_weight,
            },
            destination,
        )

    def load(self, path: str | Path) -> bool:
        """Load a previously promoted calibrator, if present."""
        destination = Path(path)
        if not destination.exists():
            return False
        payload: dict[str, Any] = joblib.load(destination)  # nosec B301
        self.calibrator = payload["calibrator"]
        self.metrics = dict(payload.get("metrics", {}))
        self.blend_weight = float(payload.get("blend_weight", self.blend_weight))
        return True
