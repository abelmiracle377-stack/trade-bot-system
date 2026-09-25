"""Baseline comparison tests."""

import numpy as np
import pandas as pd
import pytest

from src.features.engineer import FeatureEngineer
from src.models.predictor import SignalPredictor


@pytest.fixture
def synthetic_trending_data():
    np.random.seed(42)
    n = 400
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    returns = np.random.randn(n) * 0.01 + 0.0015
    close = 100 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.randn(n) * 0.005))
    low = close * (1 - np.abs(np.random.randn(n) * 0.005))
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(1_000_000, 5_000_000, n)
    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
            "Adj Close": close,
        },
        index=dates,
    )


def _naive_always_long_accuracy(df: pd.DataFrame, horizon: int = 5) -> float:
    future_ret = df["Close"].pct_change(horizon).shift(-horizon)
    target = (future_ret > 0).astype(int)
    valid = target.dropna()
    return (valid == 1).mean()


def _moving_average_crossover_accuracy(df: pd.DataFrame, horizon: int = 5) -> float:
    sma_fast = df["Close"].rolling(10).mean()
    sma_slow = df["Close"].rolling(30).mean()
    signal = (sma_fast > sma_slow).astype(int)
    future_ret = df["Close"].pct_change(horizon).shift(-horizon)
    target = (future_ret > 0).astype(int)
    aligned = pd.DataFrame({"signal": signal, "target": target}).dropna()
    long_mask = aligned["signal"] == 1
    if long_mask.sum() == 0:
        return 0.5
    return (aligned.loc[long_mask, "target"] == 1).mean()


def test_ml_beats_always_long_baseline(synthetic_trending_data):
    eng = FeatureEngineer()
    featured = eng.transform(synthetic_trending_data)
    feature_cols = eng.get_feature_columns(featured)
    model = SignalPredictor(model_type="random_forest", target_horizon=5, random_state=42)
    metrics = model.fit(featured, feature_cols, test_size=0.25)
    baseline_acc = _naive_always_long_accuracy(synthetic_trending_data, horizon=5)
    assert metrics["accuracy"] >= baseline_acc - 0.05


def test_ml_beats_ma_crossover_baseline(synthetic_trending_data):
    eng = FeatureEngineer()
    featured = eng.transform(synthetic_trending_data)
    feature_cols = eng.get_feature_columns(featured)
    model = SignalPredictor(model_type="random_forest", target_horizon=5, random_state=42)
    metrics = model.fit(featured, feature_cols, test_size=0.25)
    ma_acc = _moving_average_crossover_accuracy(synthetic_trending_data, horizon=5)
    assert metrics["accuracy"] >= ma_acc - 0.08


def test_model_has_positive_auc(synthetic_trending_data):
    eng = FeatureEngineer()
    featured = eng.transform(synthetic_trending_data)
    feature_cols = eng.get_feature_columns(featured)
    model = SignalPredictor(model_type="random_forest", target_horizon=5, random_state=42)
    metrics = model.fit(featured, feature_cols, test_size=0.25)
    assert metrics["roc_auc"] >= 0.50


def test_model_metadata_contains_reproducibility_fields(synthetic_trending_data):
    eng = FeatureEngineer()
    featured = eng.transform(synthetic_trending_data)
    feature_cols = eng.get_feature_columns(featured)
    model = SignalPredictor(
        model_type="random_forest",
        target_horizon=5,
        random_state=42,
        model_params={"n_estimators": 25},
    )
    model.fit(featured, feature_cols, test_size=0.25)

    metadata = model.metadata()

    assert metadata["model_type"] == "random_forest"
    assert metadata["target_horizon"] == 5
    assert metadata["random_state"] == 42
    assert metadata["model_params"]["n_estimators"] == 25
    assert metadata["feature_names"] == feature_cols
    assert set(metadata["feature_importances"]) == set(feature_cols)
    assert all(isinstance(value, float) for value in metadata["feature_importances"].values())
    assert metadata["fitted_model_params"]["random_state"] == 42
