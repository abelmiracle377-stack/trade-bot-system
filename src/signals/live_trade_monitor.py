"""Monitor open broker positions and produce live-trade risk signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable


@dataclass(frozen=True)
class LiveTradeSignal:
    symbol: str
    side: str
    qty: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    signal: str
    reason: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LiveTradeMonitor:
    """Analyze positions already held by the broker.

    This component is observational: it does not submit, cancel, or close orders.
    Any resulting execution decision must pass through the normal risk/execution
    layer.
    """

    def __init__(
        self,
        *,
        stop_loss_pct: float = 0.08,
        take_profit_pct: float = 0.20,
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def analyze_position(self, position: Any) -> LiveTradeSignal:
        side = str(position.side).lower()
        signed_side = "SHORT" if "short" in side else "LONG"
        entry = float(position.avg_entry_price)
        current = float(position.current_price)
        pnl = float(position.unrealized_pl)
        pnl_pct = pnl / (entry * abs(float(position.qty))) if entry > 0 else 0.0

        if pnl_pct <= -self.stop_loss_pct:
            signal, reason = "EXIT_REVIEW", "position reached configured stop-loss threshold"
        elif pnl_pct >= self.take_profit_pct:
            signal, reason = "TAKE_PROFIT_REVIEW", "position reached configured take-profit threshold"
        elif pnl_pct < 0:
            signal, reason = "HOLD_RISK", "position is currently below entry"
        else:
            signal, reason = "HOLD", "position remains profitable and below take-profit threshold"

        return LiveTradeSignal(
            symbol=str(position.symbol),
            side=signed_side,
            qty=abs(float(position.qty)),
            entry_price=entry,
            current_price=current,
            market_value=float(position.market_value),
            unrealized_pnl=pnl,
            unrealized_pnl_pct=round(pnl_pct, 6),
            signal=signal,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def analyze_positions(self, positions: Iterable[Any]) -> list[LiveTradeSignal]:
        return [self.analyze_position(position) for position in positions]
