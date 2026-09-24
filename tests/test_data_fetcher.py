"""Tests for DataFetcher (mocked to avoid network calls)."""

import pandas as pd
import pytest
from unittest.mock import patch

from src.data.fetcher import DataFetcher


@pytest.fixture
def sample_history():
    dates = pd.date_range("2023-01-01", periods=30, freq="B")
    return pd.DataFrame(
        {
            "Open": 100.0,
            "High": 102.0,
            "Low": 99.0,
            "Close": 101.0,
            "Volume": 1_000_000,
            "Adj Close": 101.0,
        },
        index=dates,
    )


def test_fetch_uses_cache(tmp_path, sample_history):
    fetcher = DataFetcher(cache_dir=str(tmp_path))
    cache_file = tmp_path / "AAPL_2023-01-01_latest_1d.parquet"
    sample_history.to_parquet(cache_file)
    with patch("yfinance.Ticker") as mock_ticker:
        result = fetcher.fetch("AAPL", start="2023-01-01", use_cache=True)
        mock_ticker.assert_not_called()
        assert len(result) == 30
        assert "Close" in result.columns


def test_fetch_multiple_handles_failure(tmp_path):
    fetcher = DataFetcher(cache_dir=str(tmp_path))
    with patch.object(fetcher, "fetch") as mock_fetch:
        mock_fetch.side_effect = [
            pd.DataFrame({"Close": [1, 2, 3]}),
            ValueError("network error"),
        ]
        result = fetcher.fetch_multiple(["AAPL", "BAD"], start="2020-01-01")
        assert "AAPL" in result
        assert "BAD" not in result


def test_get_aligned_close(tmp_path, sample_history):
    fetcher = DataFetcher(cache_dir=str(tmp_path))
    with patch.object(fetcher, "fetch") as mock_fetch:
        mock_fetch.return_value = sample_history
        aligned = fetcher.get_aligned_close(["AAPL", "MSFT"], start="2023-01-01")
        assert list(aligned.columns) == ["AAPL", "MSFT"]
        assert len(aligned) == 30
