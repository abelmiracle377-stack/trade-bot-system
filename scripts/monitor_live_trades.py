#!/usr/bin/env python3
"""Analyze currently open broker trades without submitting orders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.execution import AlpacaBroker
from src.signals.live_trade_monitor import LiveTradeMonitor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Connect to the live Alpaca account")
    parser.add_argument("--output", default="data/runtime/live_trade_signals.jsonl")
    args = parser.parse_args()

    broker = AlpacaBroker(paper=not args.live)
    monitor = LiveTradeMonitor(
        stop_loss_pct=0.08,
        take_profit_pct=0.20,
    )
    positions = broker.client.get_all_positions()
    signals = monitor.analyze_positions(positions)

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        for signal in signals:
            handle.write(json.dumps(signal.to_dict()) + "\n")

    for signal in signals:
        print(
            f"{signal.symbol}: {signal.signal} | "
            f"PnL={signal.unrealized_pnl:.2f} ({signal.unrealized_pnl_pct:.2%}) | "
            f"{signal.reason}"
        )


if __name__ == "__main__":
    main()
