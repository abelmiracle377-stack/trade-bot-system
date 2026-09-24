"""Persistent risk state for repeated trading-agent executions."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class TradingRiskState:
    trading_day: str
    peak_equity: float


class RiskStateStore:
    """Persist the intraday equity peak across agent invocations."""

    def __init__(self, path: str = "data/runtime/trading_state.json"):
        self.path = Path(path)

    def load_or_initialize(self, trading_day: date, starting_equity: float) -> TradingRiskState:
        if starting_equity <= 0:
            raise ValueError("starting_equity must be positive")

        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if payload.get("trading_day") == trading_day.isoformat():
                    peak = float(payload["peak_equity"])
                    if peak > 0:
                        return TradingRiskState(trading_day.isoformat(), max(peak, starting_equity))
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                pass

        state = TradingRiskState(trading_day.isoformat(), starting_equity)
        self.save(state)
        return state

    def save(self, state: TradingRiskState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"trading_day": state.trading_day, "peak_equity": state.peak_equity}, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
