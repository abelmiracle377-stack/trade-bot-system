#!/usr/bin/env python3
"""Apply deterministic protective exits to open Alpaca positions.

Live execution requires both --live and ALLOW_LIVE_TRADING=YES.
"""

from __future__ import annotations
import argparse
from loguru import logger
from src.execution import AlpacaBroker

def run(*, live: bool = False, stop_loss_pct: float = 0.08) -> int:
    broker = AlpacaBroker(paper=not live)
    positions = broker.client.get_all_positions()
    exits = 0
    for position in positions:
        entry = float(position.avg_entry_price)
        qty = abs(float(position.qty))
        if entry <= 0 or qty <= 0:
            continue
        pnl_pct = float(position.unrealized_pl) / (entry * qty)
        if pnl_pct <= -abs(stop_loss_pct):
            logger.warning("Protective exit for {}: pnl_pct={} threshold={}", position.symbol, pnl_pct, stop_loss_pct)
            broker.close_position(str(position.symbol))
            exits += 1
    logger.info("Protective exit cycle complete: {} position(s) closed", exits)
    return exits

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--stop-loss-pct", type=float, default=0.08)
    args = parser.parse_args()
    run(live=args.live, stop_loss_pct=args.stop_loss_pct)

if __name__ == "__main__":
    main()
