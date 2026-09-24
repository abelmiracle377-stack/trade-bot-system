"""Additional backtest performance metrics."""

import numpy as np
import pandas as pd

def sortino_ratio(
    returns: pd.Series,
    *,
    annualization: int = 252,
    risk_free_rate: float = 0.0,
) -> float:
    """Annualized Sortino ratio using downside deviation."""
    if returns.empty:
        return 0.0
    rf_period = (1.0 + risk_free_rate) ** (1.0 / annualization) - 1.0
    excess = returns - rf_period
    downside = excess.clip(upper=0.0)
    downside_dev = np.sqrt((downside ** 2).mean()) * np.sqrt(annualization)
    annualized = excess.mean() * annualization
    return float(annualized / downside_dev) if downside_dev > 0 else 0.0

def max_drawdown_duration(equity: pd.Series) -> int:
    """Return the longest number of observations below a prior peak."""
    if equity.empty:
        return 0
    peak = equity.cummax()
    underwater = equity < peak
    groups = (~underwater).cumsum()
    durations = underwater.groupby(groups).sum()
    return int(durations.max()) if not durations.empty else 0

def calmar_ratio(cagr: float, max_drawdown: float) -> float:
    """Return CAGR divided by absolute maximum drawdown."""
    denominator = abs(max_drawdown)
    return float(cagr / denominator) if denominator > 0 else 0.0
