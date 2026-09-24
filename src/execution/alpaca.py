"""Alpaca Trading API adapter.

Paper trading is the default. Live trading requires an explicit opt-in
environment variable and should only be enabled after paper validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


@dataclass(frozen=True)
class BrokerOrder:
    symbol: str
    side: str
    qty: float
    order_id: str
    status: str


class AlpacaBroker:
    """Small broker adapter around Alpaca's Trading API."""

    def __init__(self, *, paper: bool = True):
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_API_SECRET")
        if not key or not secret:
            raise RuntimeError(
                "ALPACA_API_KEY and ALPACA_API_SECRET must be set"
            )

        if not paper and os.getenv("ALLOW_LIVE_TRADING") != "YES":
            raise RuntimeError(
                "Live trading is disabled. Set ALLOW_LIVE_TRADING=YES "
                "explicitly after validating the strategy in paper trading."
            )

        self.paper = paper
        self.client = TradingClient(key, secret, paper=paper)

    def account_equity(self) -> float:
        """Return current account equity."""
        account = self.client.get_account()
        return float(account.equity)

    def position_qty(self, symbol: str) -> float:
        """Return signed position quantity; zero when no position exists."""
        try:
            position = self.client.get_open_position(symbol)
        except Exception as exc:
            if "position does not exist" in str(exc).lower():
                return 0.0
            raise
        qty = float(position.qty)
        return qty if float(position.market_value) >= 0 else -qty

    def submit_market_order(
        self,
        symbol: str,
        *,
        side: int,
        qty: float,
        client_order_id: str | None = None,
    ) -> BrokerOrder:
        """Submit a market order. side is +1 for buy and -1 for sell."""
        if side not in (-1, 1):
            raise ValueError("side must be +1 or -1")
        if qty <= 0:
            raise ValueError("qty must be positive")

        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side > 0 else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=client_order_id,
        )
        order = self.client.submit_order(order_data=request)
        return BrokerOrder(
            symbol=symbol,
            side="buy" if side > 0 else "sell",
            qty=qty,
            order_id=str(order.id),
            status=str(order.status),
        )

    def close_position(self, symbol: str) -> Any:
        """Close an existing position at market."""
        return self.client.close_position(symbol)
