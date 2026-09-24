"""Integration test for the deterministic market-data-to-backtest pipeline."""

import numpy as np
import pandas as pd

from src.backtest.engine import Backtester
from src.data.validation import validate_ohlcv
from src.features.engineer import FeatureEngineer
from src.models.predictor import SignalPredictor


def _market_data(rows: int = 180) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    trend = 100.0 + np.arange(rows) * 0.15
    seasonal = 2.0 * np.sin(np.arange(rows) / 7.0)
    close = trend + seasonal

    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Volume": np.full(rows, 1_000_000, dtype=float),
        },
        index=dates,
    )


def test_market_data_to_model_to_backtest_pipeline():
    prices = _market_data()

    # The same validation used by the data-fetching layer must accept
    # the deterministic fixture before it reaches feature engineering.
    report = validate_ohlcv(prices)
    assert report.valid, report.errors

    features = FeatureEngineer(
        lookback_windows=[5, 10, 20],
        rsi_period=14,
        bb_period=20,
        atr_period=14,
        volume_ma_period=20,
    ).transform(prices)

    feature_columns = FeatureEngineer().get_feature_columns(features)
    # Keep only features with finite values so the model receives the
    # same kind of clean rows expected after feature generation.
    usable = features[feature_columns].replace([np.inf, -np.inf], np.nan)
    feature_columns = [
        column for column in feature_columns if usable[column].notna().any()
    ]

    predictor = SignalPredictor(
        model_type="random_forest",
        target_horizon=3,
        random_state=42,
        n_estimators=40,
        max_depth=4,
        min_samples_leaf=3,
    )
    metrics = predictor.fit(features, feature_columns, test_size=0.25)

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0

    probabilities = predictor.predict_proba(features)
    signals = pd.Series(0, index=features.index, dtype=int)
    signals.loc[probabilities.index] = np.where(probabilities >= 0.5, 1, -1)

    result = Backtester(
        initial_capital=100_000.0,
        commission_pct=0.0,
        slippage_pct=0.0,
    ).run({"TEST": prices}, {"TEST": signals})

    assert not result.equity_curve.empty
    assert np.isfinite(result.equity_curve.to_numpy()).all()
    assert result.equity_curve.index.is_monotonic_increasing
    assert np.isfinite(result.metrics["final_equity"])
    assert result.metrics["n_trades"] >= 0
