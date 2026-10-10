#!/usr/bin/env python3
"""Run the TradeAI model-driven paper trading bot continuously.

The runner is paper-only: it never enables live broker execution. It reuses
scripts.run_trading_agent's risk-gated model-to-Alpaca cycle, writes a health
status file, and waits between cycles. Start with --once to validate setup.

Examples:
    python scripts/run_paper_bot.py --once
    python scripts/run_paper_bot.py --interval-seconds 3600
    python scripts/run_paper_bot.py --interval-seconds 900 --max-cycles 4
"""
from __future__ import annotations

import argparse
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from scripts.run_trading_agent import _run_cycle, _write_run_status

_STOP = False


def _request_stop(_signum: int, _frame: object) -> None:
    global _STOP
    _STOP = True


def run_bot(
    *,
    config_path: str = "config/config.yaml",
    interval_seconds: int = 3600,
    max_cycles: int = 0,
    once: bool = False,
) -> int:
    """Run paper cycles until stopped or max_cycles is reached.

    Returns the number of cycles that failed. A failed cycle is recorded and
    the runner continues on the next interval; it never switches to live mode.
    """
    if interval_seconds < 60:
        raise ValueError("interval_seconds must be at least 60 seconds")
    completed = 0
    failures = 0
    status_path = "data/runtime/last_run_status.json"
    logger.info("Starting TradeAI PAPER bot; live execution is disabled")

    while not _STOP and (max_cycles <= 0 or completed < max_cycles):
        started = time.monotonic()
        cycle_id = datetime.now(timezone.utc).isoformat()
        try:
            _run_cycle(config_path, live=False)
            _write_run_status(status_path, status="paper_ok")
            logger.info("Paper cycle {} completed", cycle_id)
        except Exception as exc:  # keep daemon alive, but persist the failure
            failures += 1
            logger.exception("Paper cycle {} failed", cycle_id)
            _write_run_status(status_path, status="paper_error", error=str(exc)[:500])
        completed += 1
        if once or _STOP or (max_cycles > 0 and completed >= max_cycles):
            break
        remaining = max(0.0, interval_seconds - (time.monotonic() - started))
        logger.info("Next paper cycle in {:.0f} seconds", remaining)
        # Short sleeps allow SIGINT/SIGTERM to stop the runner promptly.
        while remaining > 0 and not _STOP:
            step = min(remaining, 1.0)
            time.sleep(step)
            remaining -= step

    logger.info("Paper bot stopped: cycles={}, failures={}", completed, failures)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/config.yaml", help="YAML config path")
    parser.add_argument(
        "--interval-seconds", type=int, default=3600,
        help="Minimum seconds between cycles (default: 3600; minimum: 60)",
    )
    parser.add_argument("--max-cycles", type=int, default=0,
                        help="Stop after N cycles; 0 means run until interrupted")
    parser.add_argument("--once", action="store_true", help="Run one paper cycle and exit")
    args = parser.parse_args()
    if args.max_cycles < 0:
        parser.error("--max-cycles must be zero or greater")
    if args.interval_seconds < 60:
        parser.error("--interval-seconds must be at least 60")

    signal.signal(signal.SIGINT, _request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _request_stop)
    return 1 if run_bot(config_path=args.config, interval_seconds=args.interval_seconds,
                        max_cycles=args.max_cycles, once=args.once) else 0


if __name__ == "__main__":
    raise SystemExit(main())
