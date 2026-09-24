"""Unit tests for feature engineering."""

import pandas as pd
import numpy as np
import pytest
from src.features.engineer import FeatureEngineer


@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high = close + np.random.rand(100) * 2
    low = close - np.random.rand(100) * 2
    open_ = close + np.random.randn(100) * 0.3
    volume = np.random.randint(1_000_000, 5_000_000, 100)
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


def test_feature_engineer_adds_columns(sample_ohlcv):
    eng = FeatureEngineer()
    result = eng.transform(sample_ohlcv)
    assert "rsi" in result.columns
    assert "macd" in result.columns
    assert "bb_pct" in result.columns
    assert "atr" in result.columns
    assert "ret_1d" in result.columns
    assert len(result) == len(sample_ohlcv)


def test_feature_columns_excludes_ohlcv(sample_ohlcv):
    eng = FeatureEngineer()
    result = eng.transform(sample_ohlcv)
    cols = eng.get_feature_columns(result)
    for c in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
        assert c not in cols
    assert len(cols) > 10


def test_no_infinite_values(sample_ohlcv):
    eng = FeatureEngineer()
    result = eng.transform(sample_ohlcv)
    assert not np.isinf(result.select_dtypes(include=[np.number])).any().any()
