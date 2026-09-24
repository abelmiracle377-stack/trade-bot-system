#!/usr/bin/env python3
"""
Run a tracked experiment: train model, run backtest, log metrics + params.

Usage:
    python scripts/run_experiment.py --config config/config.yaml
    python scripts/run_experiment.py --config config/config.yaml --run-id exp_001
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import load_config, setup_logger
from src.data import DataFetcher
from src.features import FeatureEngineer
from src.models import SignalPredictor
from src.strategies import SignalGenerator
from src.risk import RiskManager
from src.backtest import Backtester
from loguru import logger
import pandas as pd


def run_experiment(config_path: str, run_id: str | None = None) -> dict:
    cfg = load_config(config_path)
    run_id = run_id or datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")

    setup_logger(
        level=cfg.get("logging", {}).get("level", "INFO"),
        log_file=cfg.get("logging", {}).get("file", "logs/trading_system.log"),
        structured=True,
        run_id=run_id,
    )

    logger.info(f"Starting experiment run_id={run_id}")

    # --- Data ---
    data_cfg = cfg["data"]
    fetcher = DataFetcher(cache_dir=data_cfg.get("cache_dir", "data/cache"))
    symbols = data_cfg["symbols"]
    start = data_cfg.get("start_date", "2018-01-01")
    end = data_cfg.get("end_date")

    raw_data = fetcher.fetch_multiple(symbols, start=start, end=end)
    if not raw_data:
        raise RuntimeError("No data downloaded")

    # --- Features + Model ---
    feat_cfg = cfg["features"]
    model_cfg = cfg["model"]
    strat_cfg = cfg["strategy"]

    engineer = FeatureEngineer(
        lookback_windows=feat_cfg.get("lookback_windows"),
        rsi_period=feat_cfg.get("rsi_period", 14),
    )
    signal_gen = SignalGenerator(
        long_threshold=strat_cfg.get("signal_threshold", 0.55),
        allow_short=strat_cfg.get("allow_short", False),
    )

    prices, signals, vols = {}, {}, {}
    model_metrics = {}

    for sym, df in raw_data.items():
        try:
            featured = engineer.transform(df)
            feature_cols = engineer.get_feature_columns(featured)

            predictor = SignalPredictor(
                model_type=model_cfg.get("type", "xgboost"),
                target_horizon=model_cfg.get("target_horizon", 5),
                model_params=model_cfg.get(model_cfg.get("type", "xgboost"), {}),
                random_state=model_cfg.get("random_state", 42),
            )
            metrics = predictor.fit(
                featured,
                feature_cols,
                test_size=1.0 - model_cfg.get("train_test_split", 0.8),
            )
            model_metrics[sym] = metrics

            proba = predictor.predict_proba(featured)
            signals[sym] = signal_gen.generate(proba)
            prices[sym] = featured
            vols[sym] = featured["vol_20d"].fillna(0.20)

            # Persist model
            model_path = Path(f"models/{sym}_{run_id}.joblib")
            model_path.parent.mkdir(exist_ok=True)
            predictor.save(model_path)

        except Exception as e:
            logger.exception(f"Failed processing symbol={sym}: {e}")
            continue

    # --- Backtest ---
    risk_cfg = cfg["risk"]
    bt_cfg = cfg["backtest"]

    risk_mgr = RiskManager(
        max_position_pct=risk_cfg.get("max_position_pct", 0.15),
        stop_loss_pct=risk_cfg.get("stop_loss_pct", 0.08),
        take_profit_pct=risk_cfg.get("take_profit_pct", 0.20),
        max_drawdown_pct=risk_cfg.get("max_drawdown_pct", 0.25),
        volatility_target=risk_cfg.get("volatility_target", 0.12),
    )

    backtester = Backtester(
        initial_capital=bt_cfg.get("initial_capital", 100_000.0),
        commission_pct=bt_cfg.get("commission_pct", 0.001),
        slippage_pct=bt_cfg.get("slippage_pct", 0.0005),
        risk_manager=risk_mgr,
    )

    result = backtester.run(prices=prices, signals=signals, feature_vols=vols)

    # --- Experiment log ---
    experiment_record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path,
        "symbols": symbols,
        "model_type": model_cfg.get("type"),
        "target_horizon": model_cfg.get("target_horizon"),
        "random_state": model_cfg.get("random_state", 42),
        "model_metrics": model_metrics,
        "backtest_metrics": result.metrics,
        "n_trades": result.metrics.get("n_trades", 0),
    }

    log_path = Path("reports/experiment_log.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(experiment_record, default=str) + "\n")

    logger.info(f"Experiment complete. Metrics: {result.metrics}")
    logger.info(f"Logged to {log_path}")

    # Also write a human-readable summary
    summary_path = Path(f"reports/{run_id}_summary.json")
    with open(summary_path, "w") as f:
        json.dump(experiment_record, f, indent=2, default=str)

    return experiment_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a tracked trading experiment")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML")
    parser.add_argument("--run-id", default=None, help="Optional run identifier")
    args = parser.parse_args()

    run_experiment(args.config, args.run_id)
