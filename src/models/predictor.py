"""Machine-learning signal predictor with chronological validation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier


class SignalPredictor:
    """Binary classifier for positive forward returns."""

    def __init__(
        self,
        model_type: str = "xgboost",
        target_horizon: int = 5,
        random_state: int = 42,
        model_params: Optional[Dict[str, Any]] = None,
        **extra_params: Any,
    ):
        supported = {"xgboost", "random_forest", "logistic"}
        if model_type not in supported:
            raise ValueError(f"Unsupported model_type: {model_type}")
        if target_horizon <= 0:
            raise ValueError("target_horizon must be positive")
        self.model_type = model_type
        self.target_horizon = target_horizon
        self.random_state = random_state
        self.model_params = model_params
        self.model: Any = None
        self.feature_names: List[str] = []
        self.is_fitted = False

    def _build_model(self):
        if self.model_type == "random_forest":
            params = {"n_estimators": 200, "max_depth": 10, "min_samples_leaf": 20}
            params.update(self.model_params)
            return RandomForestClassifier(random_state=self.random_state, **params)
        if self.model_type == "logistic":
            params = {"max_iter": 1000}
            params.update(self.model_params)
            return LogisticRegression(random_state=self.random_state, **params)
        params = {
            "n_estimators": 300,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "eval_metric": "logloss",
            "random_state": self.random_state,
            "n_jobs": 1,
        }
        params.update(self.model_params)
        return XGBClassifier(**params)

    def _create_target(self, df: pd.DataFrame) -> pd.Series:
        if "Close" not in df.columns:
            raise ValueError("Data must contain Close")
        forward_return = df["Close"].shift(-self.target_horizon) / df["Close"] - 1.0
        return (forward_return > 0).astype(float).where(forward_return.notna())

    def fit(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        test_size: float = 0.2,
    ) -> Dict[str, float]:
        if not 0 < test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
        missing = [c for c in feature_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")
        if not df.index.is_monotonic_increasing:
            raise ValueError("Data must be sorted chronologically")

        data = df[feature_cols].copy()
        target = self._create_target(df)
        valid = data.notna().all(axis=1) & target.notna()
        data = data.loc[valid]
        target = target.loc[valid].astype(int)
        if len(data) < 20:
            raise ValueError("Insufficient training data")

        split = int(len(data) * (1.0 - test_size))
        if split <= 0 or split >= len(data):
            raise ValueError("test_size leaves no train or test observations")
        X_train, X_test = data.iloc[:split], data.iloc[split:]
        y_train, y_test = target.iloc[:split], target.iloc[split:]

        self.feature_names = list(feature_cols)
        self.model = self._build_model()
        self.model.fit(X_train, y_train)
        self.is_fitted = True

        proba = self.model.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        metrics: Dict[str, float] = {
            "accuracy": float(accuracy_score(y_test, pred)),
        }
        if y_test.nunique() > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
        else:
            metrics["roc_auc"] = 0.5
        return metrics

    def predict_proba(self, df: pd.DataFrame) -> pd.Series:
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model is not fitted")
        missing = [c for c in self.feature_names if c not in df.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")
        X = df[self.feature_names].copy()
        valid = X.notna().all(axis=1)
        result = pd.Series(np.nan, index=df.index, dtype=float)
        if valid.any():
            result.loc[valid] = self.model.predict_proba(X.loc[valid])[:, 1]
        return result.dropna()

    def save(self, path: str | Path) -> None:
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Cannot save an unfitted model")
        payload = {
            "model_type": self.model_type,
            "target_horizon": self.target_horizon,
            "random_state": self.random_state,
            "model_params": self.model_params,
            "model": self.model,
            "feature_names": self.feature_names,
        }
        joblib.dump(payload, Path(path))

    def load(self, path: str | Path) -> None:
        # Model files are trusted local artifacts produced by this application.
        payload = joblib.load(Path(path))  # nosec B301
        self.model_type = payload["model_type"]
        self.target_horizon = payload["target_horizon"]
        self.random_state = payload["random_state"]
        self.model_params = payload.get("model_params", {})
        self.model = payload["model"]
        self.feature_names = list(payload["feature_names"])
        self.is_fitted = True
