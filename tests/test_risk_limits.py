"""Tests for deterministic hard risk limits."""

import pandas as pd
from src.risk.limits import RiskLimits, evaluate_risk

def test_daily_loss_blocks_trading():
    decision = evaluate_risk(
        equity=96_000,
        start_of_day_equity=100_000,
        peak_equity=100_000,
        gross_exposure=0,
        position_exposure=0,
        limits=RiskLimits(max_daily_loss_pct=0.03),
    )
    assert not decision.allowed
    assert "daily loss limit breached" in decision.reasons

def test_leverage_limit_blocks_trading():
    decision = evaluate_risk(
        equity=100_000,
        start_of_day_equity=100_000,
        peak_equity=100_000,
        gross_exposure=120_000,
        position_exposure=10_000,
        limits=RiskLimits(max_leverage=1.0),
    )
    assert not decision.allowed
    assert "leverage limit breached" in decision.reasons

def test_stale_data_blocks_trading():
    now = pd.Timestamp("2026-01-01 12:00", tz="UTC")
    old = pd.Timestamp("2026-01-01 08:00", tz="UTC")
    decision = evaluate_risk(
        equity=100_000,
        start_of_day_equity=100_000,
        peak_equity=100_000,
        gross_exposure=0,
        position_exposure=0,
        limits=RiskLimits(max_data_age_minutes=60),
        data_timestamp=old,
        now=now,
    )
    assert not decision.allowed
    assert "market data is stale" in decision.reasons
