"""Execution agent connecting model signals to a broker.

The agent separates signal generation from execution and applies deterministic
portfolio-level risk checks immediately before an order is submitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

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
        """Synchronize one symbol with a requested +1/0/-1 signal."""
        if signal not in (-1, 0, 1):
            raise ValueError("signal must be -1, 0, or 1")
        if price <= 0:
            raise ValueError("price must be positive")

        equity = self.broker.account_equity()
        current_qty = float(self.broker.position_qty(symbol))
        current_notional = abs(current_qty * price)
        gross_exposure = float(self.broker.gross_exposure(price))

        is_closing = signal == 0 and current_qty != 0
        target_notional = 0.0
        if signal:
            target_notional = min(
                equity * self.config.max_order_notional_pct,
                equity * self.config.max_leverage,
            )

        target_qty = signal * target_notional / price if signal else 0.0
        delta_qty = target_qty - current_qty
        delta_notional = abs(delta_qty) * price

        if delta_notional <= 0:
            logger.info("{} already at target position", symbol)
            return None

        if not is_closing and delta_notional < self.config.min_order_notional:
            logger.info("{} order is below minimum notional", symbol)
            return None

        if hasattr(self.broker, "has_open_order") and self.broker.has_open_order(symbol):
            logger.warning("Order blocked for {}: existing open order", symbol)
            return None

        prospective_gross = gross_exposure - current_notional + target_notional

        limits = RiskLimits(
            max_daily_loss_pct=self.config.max_daily_loss_pct,
            max_drawdown_pct=self.config.max_drawdown_pct,
            max_leverage=self.config.max_leverage,
            max_position_pct=self.config.max_order_notional_pct,
            max_data_age_minutes=self.config.max_data_age_minutes,
        )

        if is_closing:
            # A reduce-only action is risk-reducing and must remain available
            # when an opening-trade kill switch has fired.
            decision = evaluate_risk(
                equity=equity,
                start_of_day_equity=start_of_day_equity,
                peak_equity=peak_equity,
                gross_exposure=prospective_gross,
                position_exposure=0.0,
                limits=limits,
                data_timestamp=None,
                now=datetime.now(timezone.utc),
                allow_risk_reduction=True,
            )
        else:
            decision = evaluate_risk(
                equity=equity,
                start_of_day_equity=start_of_day_equity,
                peak_equity=peak_equity,
                gross_exposure=prospective_gross,
                position_exposure=target_notional,
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

        client_order_id = f"ai-agent-{symbol.lower()}-{uuid4().hex}"
        result = self.broker.submit_market_order(
            symbol,
            side=1 if delta_qty > 0 else -1,
            qty=abs(delta_qty),
            client_order_id=client_order_id,
        )
        logger.info(
            "Submitted {} {} {} shares; order_id={}",
            symbol,
            "BUY" if delta_qty > 0 else "SELL",
            abs(delta_qty),
            result.order_id,
        )
        return result
