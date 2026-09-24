"""Deterministic portfolio risk limits and kill-switch decisions."""

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class RiskLimits:
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.25
    max_leverage: float = 1.0
    max_position_pct: float = 0.15
    max_data_age_minutes: Optional[int] = 180


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()


def evaluate_risk(
    *,
    equity: float,
    start_of_day_equity: float,
    peak_equity: float,
    gross_exposure: float,
    position_exposure: float,
    limits: RiskLimits,
    data_timestamp: Optional[pd.Timestamp] = None,
    now: Optional[pd.Timestamp] = None,
    allow_risk_reduction: bool = False,
) -> RiskDecision:
    """Return a deterministic allow/block decision for a proposed action.

    Risk-reducing actions may bypass opening-trade kill switches and stale-data
    checks, but exposure must still be non-negative and finite.
    """
    reasons: list[str] = []
    if equity <= 0:
        reasons.append("non-positive equity")
    if gross_exposure < 0 or position_exposure < 0:
        reasons.append("negative exposure")

    if not allow_risk_reduction:
        if start_of_day_equity > 0:
            daily_loss = (equity - start_of_day_equity) / start_of_day_equity
            if daily_loss <= -limits.max_daily_loss_pct:
                reasons.append("daily loss limit breached")
        if peak_equity > 0:
            drawdown = (equity - peak_equity) / peak_equity
            if drawdown <= -limits.max_drawdown_pct:
                reasons.append("maximum drawdown breached")
        if equity > 0 and gross_exposure / equity > limits.max_leverage:
            reasons.append("leverage limit breached")
        if equity > 0 and position_exposure / equity > limits.max_position_pct:
            reasons.append("position limit breached")
        if (
            data_timestamp is not None
            and now is not None
            and limits.max_data_age_minutes is not None
        ):
            age = (now - data_timestamp).total_seconds() / 60.0
            if age > limits.max_data_age_minutes:
                reasons.append("market data is stale")

    return RiskDecision(allowed=not reasons, reasons=tuple(reasons))
