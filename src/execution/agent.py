"""Execution agent connecting model signals to a broker.

The agent deliberately separates signal generation from order execution.
It enforces the repository's deterministic risk limits immediately before
an order is submitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from src.risk.limits import RiskLimits, evaluate_risk


@dataclass(frozen=True)
class TradingAgentConfig:
    max_order_notional_pct: float = 0.15
    max_leverage: float = 1.0
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.25
    max_data_age_minutes: int = 180
    min_order_notional: float = 100.0


class TradingAgent:
    """Turn model signals into risk-checked broker orders."""

    def __init__(self, broker: Any, config: TradingAgentConfig | None = None):
        self.broker = broker
        self.config = config or TradingAgentConfig()

    def execute_signal(
        self,
        *,
        symbol: str,
        signal: int,
        price: float,
        data_timestamp: datetime,
        start_of_day_equity: float,
        peak_equity: float,
    ) -> Any | None:
        """Synchronize one symbol with the requested +1/0/-1 signal."""
        if signal not in (-1, 0, 1):
            raise ValueError("signal must be -1, 0, or 1")
        if price <= 0:
            raise ValueError("price must be positive")

        equity = self.broker.account_equity()
        current_qty = self.broker.position_qty(symbol)
        current_notional = abs(current_qty * price)

        limits = RiskLimits(
            max_daily_loss_pct=self.config.max_daily_loss_pct,
            max_drawdown_pct=self.config.max_drawdown_pct,
            max_leverage=self.config.max_leverage,
            max_position_pct=self.config.max_order_notional_pct,
            max_data_age_minutes=self.config.max_data_age_minutes,
        )
        decision = evaluate_risk(
            equity=equity,
            start_of_day_equity=start_of_day_equity,
            peak_equity=peak_equity,
            gross_exposure=current_notional,
            position_exposure=current_notional,
            limits=limits,
            data_timestamp=data_timestamp,
            now=datetime.now(timezone.utc),
        )
        if not decision.allowed:
            logger.warning(
                "Order blocked for {}: {}",
                symbol,
                "; ".join(decision.reasons),
            )
            return None

        target_notional = 0.0
        if signal:
            target_notional = min(
                equity * self.config.max_order_notional_pct,
                equity * self.config.max_leverage,
            )
            if target_notional < self.config.min_order_notional:
                logger.info("Skipping {}: target order is below minimum", symbol)
                return None

        target_qty = signal * target_notional / price if signal else 0.0
        delta_qty = target_qty - current_qty

        if abs(delta_qty) * price < self.config.min_order_notional:
            logger.info("{} already near target position; no order", symbol)
            return None

        result = self.broker.submit_market_order(
            symbol,
            side=1 if delta_qty > 0 else -1,
            qty=abs(delta_qty),
            client_order_id=f"ai-agent-{symbol.lower()}",
        )
        logger.info(
            "Submitted {} {} {} shares; order_id={}",
            symbol,
            "BUY" if delta_qty > 0 else "SELL",
            abs(delta_qty),
            result.order_id,
        )
        return result
