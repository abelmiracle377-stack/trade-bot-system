"""Tests for additional performance metrics."""

import pandas as pd
from src.backtest.metrics import calmar_ratio, max_drawdown_duration, sortino_ratio


def test_sortino_is_finite_for_mixed_returns():
    returns = pd.Series([0.01, -0.005, 0.02, -0.002, 0.01])
    assert sortino_ratio(returns) > 0


def test_drawdown_duration_counts_underwater_period():
    equity = pd.Series([100, 110, 105, 103, 112, 111])
    assert max_drawdown_duration(equity) == 2


def test_calmar_ratio():
    assert calmar_ratio(0.20, -0.10) == 2.0
