"""Basic integration-style tests for the backtester."""

import pandas as pd
import numpy as np
import pytest
from src.backtest.engine import Backtester, BacktestResult
from src.risk.manager import RiskManager


@pytest.fixture
def simple_prices_and_signals():
    dates = pd.date_range("2022-01-01", periods=60, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(60) * 0.5)

    prices = {
        "TEST": pd.DataFrame(
            {
                "Open": close,
                "High": close + 1,
                "Low": close - 1,
                "Close": close,
                "Volume": 1e6,
                "Adj Close": close,
            },
            index=dates,
        )
    }

    # Alternating long / flat signal
    sig = pd.Series(0, index=dates)
    sig.iloc[10:20] = 1
    sig.iloc[30:40] = 1
    signals = {"TEST": sig}

    vols = {"TEST": pd.Series(0.20, index=dates)}
    return prices, signals, vols


def test_backtest_runs_and_returns_metrics(simple_prices_and_signals):
    prices, signals, vols = simple_prices_and_signals
    risk = RiskManager(max_position_pct=0.2, stop_loss_pct=0.15, max_drawdown_pct=0.5)
    bt = Backtester(initial_capital=100_000, commission_pct=0.001, risk_manager=risk)

    result = bt.run(prices=prices, signals=signals, feature_vols=vols)

    assert isinstance(result, BacktestResult)
    assert len(result.equity_curve) > 10
    assert "total_return" in result.metrics
    assert "sharpe" in result.metrics
    assert "max_drawdown" in result.metrics
    assert result.metrics["final_equity"] > 0


def test_empty_signals_no_crash(simple_prices_and_signals):
    prices, _, vols = simple_prices_and_signals
    signals = {"TEST": pd.Series(0, index=prices["TEST"].index)}
    bt = Backtester(initial_capital=50_000)
    result = bt.run(prices=prices, signals=signals, feature_vols=vols)
    assert result.metrics["n_trades"] == 0
    # Equity should stay near initial capital (minus tiny costs if any)
    assert abs(result.equity_curve.iloc[-1] - 50_000) < 100
