"""Regression tests for deterministic backtest cash accounting."""

import numpy as np
import pandas as pd

from src.backtest.engine import Backtester
from src.risk.manager import RiskManager


def test_long_trade_does_not_double_charge_cash():
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    close = np.full(12, 100.0)
    close[2:] = 110.0
    prices = {
        "TEST": pd.DataFrame(
            {
                "Open": close,
                "High": close,
                "Low": close,
                "Close": close,
                "Volume": 1_000_000,
            },
            index=dates,
        )
    }
    signal = pd.Series(0, index=dates, dtype=int)
    signal.iloc[2:4] = 1

    risk = RiskManager(max_position_pct=0.20, stop_loss_pct=0.50, max_drawdown_pct=0.90)
    result = Backtester(
        initial_capital=100_000.0,
        commission_pct=0.0,
        slippage_pct=0.0,
        risk_manager=risk,
    ).run(prices, {"TEST": signal})

    assert result.metrics["final_equity"] == 102_000.0


def test_short_trade_cash_accounting_is_symmetric():
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    close = np.full(12, 100.0)
    close[2:] = 90.0
    prices = {
        "TEST": pd.DataFrame(
            {
                "Open": close,
                "High": close,
                "Low": close,
                "Close": close,
                "Volume": 1_000_000,
            },
            index=dates,
        )
    }
    signal = pd.Series(0, index=dates, dtype=int)
    signal.iloc[2:4] = -1

    risk = RiskManager(
        max_position_pct=0.20,
        stop_loss_pct=0.50,
        max_drawdown_pct=0.90,
    )
    result = Backtester(
        initial_capital=100_000.0,
        commission_pct=0.0,
        slippage_pct=0.0,
        risk_manager=risk,
    ).run(prices, {"TEST": signal})

    assert result.metrics["final_equity"] == 102_000.0
