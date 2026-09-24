#!/usr/bin/env python3
"""Run one model-to-broker trading cycle.

Paper trading is the default. Live trading requires:
    --live
and:
    ALLOW_LIVE_TRADING=YES

Never put broker credentials in source control.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from src.data import DataFetcher
from src.features import FeatureEngineer
from src.models import SignalPredictor
from src.execution import (
    AlpacaBroker,
    RiskStateStore,
    TradingAgent,
    TradingAgentConfig,
)
from src.utils import assert_valid_config, load_config, setup_logger


def run(config_path: str = "config/config.yaml", *, live: bool = False) -> None:
    cfg = load_config(config_path)
    assert_valid_config(cfg)
    setup_logger(
        level=cfg.get("logging", {}).get("level", "INFO"),
        log_file=cfg.get("logging", {}).get("file", "logs/trading_agent.log"),
    )

    broker = AlpacaBroker(paper=not live)
    agent = TradingAgent(
        broker,
        TradingAgentConfig(
            max_order_notional_pct=cfg["risk"].get("max_position_pct", 0.15),
            max_leverage=cfg["risk"].get("max_portfolio_leverage", 1.0),
            max_daily_loss_pct=cfg["risk"].get("max_daily_loss_pct", 0.03),
            max_drawdown_pct=cfg["risk"].get("max_drawdown_pct", 0.25),
            max_data_age_minutes=cfg["risk"].get("max_data_age_minutes", 5760),
        ),
    )

    # Alpaca exposes the previous account equity, so the daily-loss baseline
    # survives process restarts. The peak is persisted locally across cycles.
    now = datetime.now(timezone.utc)
    account_equity = broker.account_equity()
    start_of_day_equity = broker.previous_day_equity()
    state_store = RiskStateStore(cfg["risk"].get("state_file", "data/runtime/trading_state.json"))
    state = state_store.load_or_initialize(now.date(), account_equity)
    peak_equity = max(state.peak_equity, account_equity)
    state.peak_equity = peak_equity
    state_store.save(state)

    fetcher = DataFetcher(cache_dir=cfg["data"].get("cache_dir", "data/cache"))
    engineer = FeatureEngineer(
        lookback_windows=cfg["features"].get("lookback_windows"),
        rsi_period=cfg["features"].get("rsi_period", 14),
        macd_fast=cfg["features"].get("macd_fast", 12),
        macd_slow=cfg["features"].get("macd_slow", 26),
        macd_signal=cfg["features"].get("macd_signal", 9),
        bb_period=cfg["features"].get("bb_period", 20),
        bb_std=cfg["features"].get("bb_std", 2.0),
        atr_period=cfg["features"].get("atr_period", 14),
        volume_ma_period=cfg["features"].get("volume_ma_period", 20),
    )
    model_cfg = cfg["model"]
    strat_cfg = cfg["strategy"]

    for symbol in cfg["data"]["symbols"]:
        df = fetcher.fetch(
            symbol,
            start=cfg["data"].get("start_date", "2018-01-01"),
            end=cfg["data"].get("end_date"),
            interval=cfg["data"].get("interval", "1d"),
        )
        featured = engineer.transform(df)
        feature_cols = engineer.get_feature_columns(featured)

        predictor = SignalPredictor(
            model_type=model_cfg.get("type", "xgboost"),
            target_horizon=model_cfg.get("target_horizon", 5),
            model_params=model_cfg.get(model_cfg.get("type", "xgboost"), {}),
            random_state=model_cfg.get("random_state", 42),
        )
        predictor.fit(
            featured,
            feature_cols,
            test_size=1.0 - model_cfg.get("train_test_split", 0.8),
        )

        probabilities = predictor.predict_proba(featured)
        latest_probability = float(probabilities.iloc[-1])
        threshold = strat_cfg.get("signal_threshold", 0.55)
        short_threshold = strat_cfg.get("short_threshold", 0.45)
        allow_short = strat_cfg.get("allow_short", False)

        if latest_probability >= threshold:
            signal = 1
        elif allow_short and latest_probability <= short_threshold:
            signal = -1
        else:
            signal = 0

        latest_timestamp = featured.index[-1]
        if latest_timestamp.tzinfo is None:
            data_timestamp = latest_timestamp.tz_localize(timezone.utc).to_pydatetime()
        else:
            data_timestamp = latest_timestamp.to_pydatetime()

        result = agent.execute_signal(
            symbol=symbol,
            signal=signal,
            price=float(featured["Close"].iloc[-1]),
            data_timestamp=data_timestamp,
            start_of_day_equity=start_of_day_equity,
            peak_equity=peak_equity,
        )
        if result is not None:
            peak_equity = max(peak_equity, broker.account_equity())
            state.peak_equity = peak_equity
            state_store.save(state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live Alpaca credentials. Requires ALLOW_LIVE_TRADING=YES.",
    )
    args = parser.parse_args()
    run(args.config, live=args.live)


if __name__ == "__main__":
    main()
