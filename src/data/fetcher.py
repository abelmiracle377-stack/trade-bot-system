"""Market data fetching and caching."""

from pathlib import Path
from typing import List, Optional
import pandas as pd
import yfinance as yf
from loguru import logger
from .validation import validate_ohlcv


class DataFetcher:
    """Fetch and cache OHLCV data for multiple symbols."""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, symbol: str, start: str, end: Optional[str], interval: str) -> Path:
        end_str = end or "latest"
        return self.cache_dir / f"{symbol}_{start}_{end_str}_{interval}.parquet"

    def fetch(
        self,
        symbol: str,
        start: str = "2018-01-01",
        end: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single symbol.
        Returns DataFrame with columns: Open, High, Low, Close, Volume, Adj Close
        """
        cache_file = self._cache_path(symbol, start, end, interval)

        if use_cache and cache_file.exists():
            logger.debug(f"Loading {symbol} from cache: {cache_file}")
            df = pd.read_parquet(cache_file)
            return df

        logger.info(f"Downloading {symbol} from {start} to {end or 'today'} ({interval})")
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=interval, auto_adjust=False)

        if df.empty:
            raise ValueError(f"No data returned for {symbol}")

        # Standardize column names
        df = df.rename(columns=str.title)
        df.index.name = "Date"
        df = df[["Open", "High", "Low", "Close", "Volume", "Adj Close"]].copy()
        df = df.dropna(subset=["Close"])
        report = validate_ohlcv(df)
        report.raise_if_invalid()
        for warning in report.warnings:
            logger.warning(f"{symbol} data-quality warning: {warning}")

        if use_cache:
            df.to_parquet(cache_file)
            logger.debug(f"Cached {symbol} → {cache_file}")

        return df

    def fetch_multiple(
        self,
        symbols: List[str],
        start: str = "2018-01-01",
        end: Optional[str] = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols. Returns {symbol: DataFrame}."""
        data = {}
        for symbol in symbols:
            try:
                data[symbol] = self.fetch(symbol, start, end, interval, use_cache)
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
        return data

    def get_aligned_close(
        self,
        symbols: List[str],
        start: str = "2018-01-01",
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return a DataFrame of adjusted closes aligned on common dates."""
        frames = []
        for symbol in symbols:
            df = self.fetch(symbol, start, end)
            frames.append(df["Adj Close"].rename(symbol))
        aligned = pd.concat(frames, axis=1).dropna(how="any")
        return aligned
