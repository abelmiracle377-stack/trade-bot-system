"""Unit tests for risk manager."""

import pandas as pd

from src.risk.manager import RiskManager


def test_volatility_target_size():
    rm = RiskManager(max_position_pct=0.20, volatility_target=0.15)
    size = rm.volatility_target_size(asset_vol=0.30, portfolio_value=100_000, signal=1)
    assert size > 0
    assert size <= 0.20 * 100_000


def test_stops():
    rm = RiskManager(stop_loss_pct=0.05, take_profit_pct=0.10)
    assert rm.apply_stops(entry_price=100, current_price=94, side=1) is True
    assert rm.apply_stops(entry_price=100, current_price=111, side=1) is True
    assert rm.apply_stops(entry_price=100, current_price=102, side=1) is False


def test_drawdown_check():
    rm = RiskManager(max_drawdown_pct=0.15)
    equity = pd.Series([100, 110, 105, 90, 85])
    assert rm.check_drawdown(equity) is True
    equity2 = pd.Series([100, 105, 102, 108])
    assert rm.check_drawdown(equity2) is False


def test_normalize_weights():
    rm = RiskManager(max_portfolio_leverage=1.0)
    weights = {"A": 0.8, "B": 0.6}
    normed = rm.normalize_weights(weights)
    assert abs(sum(abs(v) for v in normed.values()) - 1.0) < 1e-6
