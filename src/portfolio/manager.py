"""Simple multi-asset portfolio construction."""

from typing import Dict, List
import pandas as pd
import numpy as np
from loguru import logger


class PortfolioManager:
    """
    Combines signals across assets and produces target weights.
    Currently supports equal-risk and signal-strength weighting.
    """

    def __init__(self, max_weight: float = 0.15, method: str = "equal_risk"):
        self.max_weight = max_weight
        self.method = method

    def construct(
        self,
        signals: Dict[str, pd.Series],
        vols: Dict[str, pd.Series],
        date: pd.Timestamp,
    ) -> Dict[str, float]:
        """
        Return target portfolio weights for a given date.
        Weight is positive for long, negative for short.
        """
        active = {}
        for sym, sig in signals.items():
            if date not in sig.index:
                continue
            s = int(sig.loc[date])
            if s == 0:
                continue
            vol = vols.get(sym)
            if vol is None or date not in vol.index or vol.loc[date] <= 0:
                vol_val = 0.20
            else:
                vol_val = float(vol.loc[date])

            if self.method == "equal_risk":
                # Inverse volatility weighting
                raw = s / vol_val
            else:
                raw = float(s)

            active[sym] = raw

        if not active:
            return {}

        # Normalize absolute exposure to 1.0 then clip per-asset
        total_abs = sum(abs(v) for v in active.values())
        weights = {k: (v / total_abs) for k, v in active.items()}
        weights = {k: np.clip(w, -self.max_weight, self.max_weight) for k, w in weights.items()}

        # Re-normalize after clipping
        total_abs = sum(abs(v) for v in weights.values())
        if total_abs > 0:
            weights = {k: v / total_abs for k, v in weights.items()}

        return weights
