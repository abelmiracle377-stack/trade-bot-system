"""Risk management: position sizing, stops, drawdown control."""

from typing import Dict, Optional
import numpy as np
import pandas as pd
from loguru import logger


class RiskManager:
    """
    Position sizing (volatility targeting + fractional Kelly) and
    portfolio-level risk constraints.
    """

    def __init__(
        self,
        max_position_pct: float = 0.15,
        max_portfolio_leverage: float = 1.0,
        stop_loss_pct: float = 0.08,
        take_profit_pct: float = 0.20,
        max_drawdown_pct: float = 0.25,
        volatility_target: float = 0.12,
        kelly_fraction: float = 0.25,
        risk_free_rate: float = 0.04,
    ):
        self.max_position_pct = max_position_pct
        self.max_portfolio_leverage = max_portfolio_leverage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.volatility_target = volatility_target
        self.kelly_fraction = kelly_fraction
        self.risk_free_rate = risk_free_rate

    def volatility_target_size(
        self,
        asset_vol: float,
        portfolio_value: float,
        signal: int,
    ) -> float:
        """
        Size position so that expected contribution to portfolio vol ≈ target.
        Returns dollar amount (positive for long, negative for short).
        """
        if asset_vol <= 0 or signal == 0:
            return 0.0

        # Target dollar risk
        target_risk = self.volatility_target * portfolio_value
        # Position size that produces that risk
        raw_size = target_risk / asset_vol
        # Apply max position constraint
        max_size = self.max_position_pct * portfolio_value
        size = np.clip(raw_size, -max_size, max_size)
        return size * signal  # sign by signal direction

    def kelly_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        portfolio_value: float,
        signal: int,
    ) -> float:
        """Fractional Kelly position sizing."""
        if avg_loss == 0 or signal == 0:
            return 0.0
        b = avg_win / abs(avg_loss)
        q = 1 - win_rate
        kelly = win_rate - (q / b)
        kelly = max(kelly, 0.0) * self.kelly_fraction
        size = kelly * portfolio_value
        max_size = self.max_position_pct * portfolio_value
        size = min(size, max_size)
        return size * signal

    def apply_stops(
        self,
        entry_price: float,
        current_price: float,
        side: int,
    ) -> bool:
        """
        Return True if stop-loss or take-profit is hit.
        side: +1 long, -1 short
        """
        if side == 0 or entry_price <= 0:
            return False

        pnl_pct = side * (current_price / entry_price - 1.0)

        if pnl_pct <= -self.stop_loss_pct:
            logger.debug(f"Stop-loss hit: {pnl_pct:.2%}")
            return True
        if pnl_pct >= self.take_profit_pct:
            logger.debug(f"Take-profit hit: {pnl_pct:.2%}")
            return True
        return False

    def check_drawdown(self, equity_curve: pd.Series) -> bool:
        """Return True if max drawdown limit is breached."""
        if equity_curve.empty:
            return False
        peak = equity_curve.cummax()
        dd = (equity_curve - peak) / peak
        max_dd = dd.min()
        if max_dd <= -self.max_drawdown_pct:
            logger.warning(f"Max drawdown breached: {max_dd:.2%}")
            return True
        return False

    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Scale weights so total absolute exposure ≤ max_portfolio_leverage."""
        total_abs = sum(abs(w) for w in weights.values())
        if total_abs <= 0:
            return weights
        scale = min(1.0, self.max_portfolio_leverage / total_abs)
        return {k: v * scale for k, v in weights.items()}
