"""Regression tests for target/feature leakage."""

import numpy as np
import pandas as pd
from src.models.predictor import SignalPredictor

def test_target_uses_future_close_without_mutating_features():
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    close = np.arange(100.0, 130.0)
    df = pd.DataFrame({"Close": close, "feature": np.arange(30.0)}, index=dates)
    predictor = SignalPredictor(model_type="logistic", target_horizon=3)
    target = predictor._create_target(df)
    assert target.iloc[-3:].isna().all()
    assert target.iloc[:-3].notna().all()
    assert "target" not in df.columns
