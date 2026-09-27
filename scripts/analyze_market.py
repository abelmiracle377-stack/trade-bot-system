#!/usr/bin/env python3
"""Run the stock/crypto market-signal agent."""

from __future__ import annotations

import argparse

from src.signals import MarketSignalAgent, send_webhook, write_signals
from src.utils import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--symbols", nargs="*", help="Override configured analysis symbols")
    parser.add_argument("--output", default="data/runtime/signals/latest.jsonl")
    parser.add_argument("--send", action="store_true", help="Send signals to SIGNAL_WEBHOOK_URL")
    args = parser.parse_args()

    cfg = load_config(args.config)
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    strategy_cfg = cfg["strategy"]

    symbols = args.symbols or data_cfg.get("analysis_symbols", data_cfg["symbols"])
    agent = MarketSignalAgent(
        model_type=model_cfg.get("type", "xgboost"),
        target_horizon=int(model_cfg.get("target_horizon", 5)),
        model_params=model_cfg.get(model_cfg.get("type", "xgboost"), {}),
        train_test_split=float(model_cfg.get("train_test_split", 0.8)),
        random_state=int(model_cfg.get("random_state", 42)),
        threshold=float(strategy_cfg.get("signal_threshold", 0.55)),
        short_threshold=float(strategy_cfg.get("short_threshold", 0.45)),
        allow_short=bool(strategy_cfg.get("allow_short", False)),
    )
    signals = agent.analyze_many(
        symbols,
        start=data_cfg.get("start_date", "2018-01-01"),
        end=data_cfg.get("end_date"),
        interval=data_cfg.get("interval", "1d"),
    )
    write_signals(signals, args.output)
    if args.send:
        send_webhook(signals)


if __name__ == "__main__":
    main()
