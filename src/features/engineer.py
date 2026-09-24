"""Feature engineering: technical indicators + custom features."""

from typing import List, Optional
import numpy as np
import pandas as pd
from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
from loguru import logger


class FeatureEngineer:
    """Generate a rich feature set from OHLCV data."""

    def __init__(
        self,
        lookback_windows: Optional[List[int]] = None,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        atr_period: int = 14,
        volume_ma_period: int = 20,
    ):
        self.lookback_windows = lookback_windows or [5, 10, 20, 50]
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.volume_ma_period = volume_ma_period

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical and custom features to OHLCV DataFrame.
        Expects columns: Open, High, Low, Close, Volume, Adj Close
        """
        data = df.copy()
        close = data["Close"]
        high = data["High"]
        low = data["Low"]
        volume = data["Volume"]

        # --- Trend ---
        for w in self.lookback_windows:
            data[f"sma_{w}"] = SMAIndicator(close, window=w).sma_indicator()
            data[f"ema_{w}"] = EMAIndicator(close, window=w).ema_indicator()
            data[f"price_to_sma_{w}"] = close / data[f"sma_{w}"] - 1.0

        macd = MACD(close, window_slow=self.macd_slow, window_fast=self.macd_fast, window_sign=self.macd_signal)
        data["macd"] = macd.macd()
        data["macd_signal"] = macd.macd_signal()
        data["macd_hist"] = macd.macd_diff()

        data["adx"] = ADXIndicator(high, low, close, window=14).adx()

        # --- Momentum ---
        data["rsi"] = RSIIndicator(close, window=self.rsi_period).rsi()
        stoch = StochasticOscillator(high, low, close)
        data["stoch_k"] = stoch.stoch()
        data["stoch_d"] = stoch.stoch_signal()
        data["roc_10"] = ROCIndicator(close, window=10).roc()

        # --- Volatility ---
        bb = BollingerBands(close, window=self.bb_period, window_dev=self.bb_std)
        data["bb_high"] = bb.bollinger_hband()
        data["bb_low"] = bb.bollinger_lband()
        data["bb_mid"] = bb.bollinger_mavg()
        data["bb_pct"] = bb.bollinger_pband()
        data["bb_width"] = (data["bb_high"] - data["bb_low"]) / data["bb_mid"]

        data["atr"] = AverageTrueRange(high, low, close, window=self.atr_period).average_true_range()
        data["atr_pct"] = data["atr"] / close

        # --- Volume ---
        data["obv"] = OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        data["volume_sma"] = volume.rolling(self.volume_ma_period).mean()
        data["volume_ratio"] = volume / data["volume_sma"]

        # --- Returns & volatility features ---
        data["ret_1d"] = close.pct_change(1)
        data["ret_5d"] = close.pct_change(5)
        data["ret_20d"] = close.pct_change(20)
        data["vol_20d"] = data["ret_1d"].rolling(20).std() * np.sqrt(252)

        # Lagged returns
        for lag in [1, 2, 3, 5]:
            data[f"ret_lag_{lag}"] = data["ret_1d"].shift(lag)

        # --- Target (forward return) – will be used by model ---
        # Note: target is created later in the pipeline with configurable horizon

        # Clean up
        data = data.replace([np.inf, -np.inf], np.nan)
        feature_cols = [c for c in data.columns if c not in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]]
        logger.debug(f"Generated {len(feature_cols)} features")
        return data

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Return list of engineered feature column names."""
        exclude = {"Open", "High", "Low", "Close", "Volume", "Adj Close", "target", "signal"}
        return [c for c in df.columns if c not in exclude]
