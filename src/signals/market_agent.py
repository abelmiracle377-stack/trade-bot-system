"""Market-analysis agent for stock and crypto signals.

This module generates research signals only. It does not place orders.
Signals are based on the repository's existing feature engineering and ML
predictor and are intended as decision support, not guaranteed forecasts.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from urllib.request import Request, urlopen

from loguru import logger

from src.data import DataFetcher
from src.features import FeatureEngineer
from src.models import SignalPredictor


@dataclass(frozen=True)
class MarketSignal:
    symbol: str
    asset_class: str
    signal: str
    probability_up: float
    confidence: float
    price: float
    timestamp: str
    model: str
    horizon_bars: int
    metrics: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


class MarketSignalAgent:
    """Analyze configured stock/crypto symbols and emit structured signals."""

    def __init__(
        self,
        *,
        data_fetcher: DataFetcher | None = None,
        feature_engineer: FeatureEngineer | None = None,
        model_type: str = "xgboost",
        target_horizon: int = 5,
        model_params: dict | None = None,
        train_test_split: float = 0.8,
        random_state: int = 42,
        threshold: float = 0.55,
        short_threshold: float = 0.45,
        allow_short: bool = False,
    ):
        self.fetcher = data_fetcher or DataFetcher()
        self.engineer = feature_engineer or FeatureEngineer()
        self.model_type = model_type
        self.target_horizon = target_horizon
        self.model_params = model_params or {}
        self.train_test_split = train_test_split
        self.random_state = random_state
        self.threshold = threshold
        self.short_threshold = short_threshold
        self.allow_short = allow_short

    @staticmethod
    def asset_class(symbol: str) -> str:
        return "crypto" if symbol.upper().endswith(("-USD", "USDT", "BTC", "ETH")) else "stock"

    def analyze(
        self,
        symbol: str,
        *,
        start: str = "2018-01-01",
        end: str | None = None,
        interval: str = "1d",
    ) -> MarketSignal:
        df = self.fetcher.fetch(symbol, start=start, end=end, interval=interval)
        featured = self.engineer.transform(df)
        feature_cols = self.engineer.get_feature_columns(featured)

        predictor = SignalPredictor(
            model_type=self.model_type,
            target_horizon=self.target_horizon,
            model_params=self.model_params,
            random_state=self.random_state,
        )
        metrics = predictor.fit(
            featured,
            feature_cols,
            test_size=1.0 - self.train_test_split,
        )
        probability = float(predictor.predict_proba(featured).iloc[-1])
        if probability >= self.threshold:
            signal = "BUY"
        elif self.allow_short and probability <= self.short_threshold:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = abs(probability - 0.5) * 2.0
        return MarketSignal(
            symbol=symbol,
            asset_class=self.asset_class(symbol),
            signal=signal,
            probability_up=round(probability, 4),
            confidence=round(confidence, 4),
            price=float(featured["Close"].iloc[-1]),
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=self.model_type,
            horizon_bars=self.target_horizon,
            metrics={k: round(float(v), 4) for k, v in metrics.items()},
        )

    def analyze_many(
        self,
        symbols: Iterable[str],
        *,
        start: str = "2018-01-01",
        end: str | None = None,
        interval: str = "1d",
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> list[MarketSignal]:
        results: list[MarketSignal] = []
        for symbol in symbols:
            try:
                result = self.analyze(symbol, start=start, end=end, interval=interval)
                results.append(result)
                logger.info(
                    "Signal {} {} probability_up={} confidence={}",
                    result.symbol,
                    result.signal,
                    result.probability_up,
                    result.confidence,
                )
            except Exception as exc:
                logger.exception("Signal analysis failed for {}: {}", symbol, exc)
                if on_error:
                    on_error(symbol, exc)
        return results


def write_signals(signals: Iterable[MarketSignal], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        for signal in signals:
            handle.write(json.dumps(signal.to_dict()) + "\n")


def send_webhook(signals: Iterable[MarketSignal], url: str | None = None) -> None:
    """Send a JSON signal batch to an optional HTTPS webhook."""
    target = url or os.getenv("SIGNAL_WEBHOOK_URL")
    if not target:
        return
    payload = json.dumps({"signals": [s.to_dict() for s in signals]}).encode("utf-8")
    request = Request(
        target,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:  # nosec B310 - configured user webhook
        if response.status >= 300:
            raise RuntimeError(f"Signal webhook returned HTTP {response.status}")
