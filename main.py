#!/usr/bin/env python3
"""
AI Trading System – End-to-End Pipeline
---------------------------------------
1. Load config
2. Fetch market data
3. Engineer features
4. Train ML signal model (per asset or multi-asset)
5. Generate signals
6. Run backtest with risk management
7. Report performance metrics

For tracked experiments with logging see: python scripts/run_experiment.py
"""

from pathlib import Path

from src.utils import load_config, setup_logger, assert_valid_config
from src.data import DataFetcher
from src.features import FeatureEngineer
from src.models import SignalPredictor
from src.strategies import SignalGenerator
from src.risk import RiskManager
from src.backtest import Backtester
from loguru import logger
import pandas as pd
import matplotlib.pyplot as plt


def run_pipeline(config_path: str = "config/config.yaml"):
    cfg = load_config(config_path)
    assert_valid_config(cfg)
    setup_logger(
        level=cfg.get("logging", {}).get("level", "INFO"),
        log_file=cfg.get("logging", {}).get("file", "logs/trading_system.log"),
    )

    logger.info("=" * 60)
    logger.info("AI Trading System – Starting pipeline")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. Data
    # ------------------------------------------------------------------
    data_cfg = cfg["data"]
    fetcher = DataFetcher(cache_dir=data_cfg.get("cache_dir", "data/cache"))
    symbols = data_cfg["symbols"]
    start = data_cfg.get("start_date", "2018-01-01")
    end = data_cfg.get("end_date")

    logger.info(f"Fetching data for {symbols} from {start}")
    raw_data = fetcher.fetch_multiple(symbols, start=start, end=end)

    if not raw_data:
        logger.error("No data downloaded – aborting")
        return

    # ------------------------------------------------------------------
    # 2. Features + Model training (per symbol for simplicity)
    # ------------------------------------------------------------------
    feat_cfg = cfg["features"]
    model_cfg = cfg["model"]
    strat_cfg = cfg["strategy"]

    engineer = FeatureEngineer(
        lookback_windows=feat_cfg.get("lookback_windows"),
        rsi_period=feat_cfg.get("rsi_period", 14),
        macd_fast=feat_cfg.get("macd_fast", 12),
        macd_slow=feat_cfg.get("macd_slow", 26),
        macd_signal=feat_cfg.get("macd_signal", 9),
        bb_period=feat_cfg.get("bb_period", 20),
        bb_std=feat_cfg.get("bb_std", 2.0),
        atr_period=feat_cfg.get("atr_period", 14),
        volume_ma_period=feat_cfg.get("volume_ma_period", 20),
    )

    signal_gen = SignalGenerator(
        long_threshold=strat_cfg.get("signal_threshold", 0.55),
        short_threshold=strat_cfg.get("short_threshold", 0.45),
        allow_short=strat_cfg.get("allow_short", False),
    )

    prices = {}
    signals = {}
    vols = {}
    models = {}

    for sym, df in raw_data.items():
        try:
            logger.info(f"Processing {sym} …")
            featured = engineer.transform(df)
            feature_cols = engineer.get_feature_columns(featured)

            predictor = SignalPredictor(
                model_type=model_cfg.get("type", "xgboost"),
                target_horizon=model_cfg.get("target_horizon", 5),
                model_params=model_cfg.get(model_cfg.get("type", "xgboost"), {}),
                random_state=model_cfg.get("random_state", 42),
            )

            _metrics = predictor.fit(
                featured,
                feature_cols,
                test_size=1.0 - model_cfg.get("train_test_split", 0.8),
            )
            logger.info(f"{sym} model metrics: {metrics}")
            models[sym] = predictor

            # Full-period probabilities → signals
            proba = predictor.predict_proba(featured)
            sig = signal_gen.generate(proba)
            signals[sym] = sig
            prices[sym] = featured  # keep full OHLCV + features

            # Realized volatility for sizing
            vols[sym] = featured["vol_20d"].fillna(0.20)

            # Persist model
            model_path = Path(f"models/{sym}_predictor.joblib")
            model_path.parent.mkdir(exist_ok=True)
            predictor.save(model_path)
        except Exception as e:
            logger.exception(f"Failed processing symbol={sym}: {e}")
            continue

    # ------------------------------------------------------------------
    # 3. Backtest
    # ------------------------------------------------------------------
    risk_cfg = cfg["risk"]
    bt_cfg = cfg["backtest"]

    risk_mgr = RiskManager(
        max_position_pct=risk_cfg.get("max_position_pct", 0.15),
        max_portfolio_leverage=risk_cfg.get("max_portfolio_leverage", 1.0),
        stop_loss_pct=risk_cfg.get("stop_loss_pct", 0.08),
        take_profit_pct=risk_cfg.get("take_profit_pct", 0.20),
        max_drawdown_pct=risk_cfg.get("max_drawdown_pct", 0.25),
        volatility_target=risk_cfg.get("volatility_target", 0.12),
        kelly_fraction=risk_cfg.get("kelly_fraction", 0.25),
    )

    backtester = Backtester(
        initial_capital=bt_cfg.get("initial_capital", 100_000.0),
        commission_pct=bt_cfg.get("commission_pct", 0.001),
        slippage_pct=bt_cfg.get("slippage_pct", 0.0005),
        risk_manager=risk_mgr,
    )

    logger.info("Running backtest …")
    result = backtester.run(prices=prices, signals=signals, feature_vols=vols)

    # ------------------------------------------------------------------
    # 4. Report
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)
    for k, v in result.metrics.items():
        if isinstance(v, float):
            if "return" in k or "cagr" in k or "drawdown" in k or "rate" in k:
                logger.info(f"  {k:20s}: {v:8.2%}")
            elif "sharpe" in k or "factor" in k:
                logger.info(f"  {k:20s}: {v:8.2f}")
            else:
                logger.info(f"  {k:20s}: {v:12.2f}")
        else:
            logger.info(f"  {k:20s}: {v}")

    # Save equity curve plot
    Path("reports").mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    result.equity_curve.plot(ax=ax, title="Equity Curve – AI Trading System")
    ax.set_ylabel("Portfolio Value ($)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("reports/equity_curve.png", dpi=150)
    logger.info("Equity curve saved → reports/equity_curve.png")

    # Save trades summary
    if result.trades:
        trades_df = pd.DataFrame([
            {
                "symbol": t.symbol,
                "entry": t.entry_date,
                "exit": t.exit_date,
                "side": "LONG" if t.side > 0 else "SHORT",
                "entry_px": t.entry_price,
                "exit_px": t.exit_price,
                "pnl": t.pnl,
                "return_pct": t.return_pct,
            }
            for t in result.trades
        ])
        trades_df.to_csv("reports/trades.csv", index=False)
        logger.info(f"Trades saved → reports/trades.csv ({len(trades_df)} trades)")

    logger.info("Pipeline finished successfully.")
    return result


if __name__ == "__main__":
    run_pipeline()
