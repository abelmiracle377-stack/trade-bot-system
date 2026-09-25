"""Tests for OHLCV data-quality validation."""

import pandas as pd
from src.data.validation import validate_ohlcv


def _valid_frame():
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    return pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0],
            "High": [11.0, 12.0, 13.0],
            "Low": [9.0, 10.0, 11.0],
            "Close": [10.5, 11.5, 12.5],
            "Volume": [100, 120, 110],
        },
        index=idx,
    )


def test_valid_ohlcv():
    assert validate_ohlcv(_valid_frame()).valid


def test_duplicate_timestamps_rejected():
    df = _valid_frame()
    df.index = [df.index[0], df.index[0], df.index[2]]
    report = validate_ohlcv(df)
    assert not report.valid
    assert any("duplicate" in e.lower() for e in report.errors)


def test_invalid_ohlc_relationship_rejected():
    df = _valid_frame()
    df.loc[df.index[0], "Low"] = 12.0
    report = validate_ohlcv(df)
    assert not report.valid
    assert any("OHLC" in e for e in report.errors)
