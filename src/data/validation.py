"""Market-data quality validation utilities."""

from dataclasses import dataclass, field
from typing import List

import pandas as pd

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


@dataclass
class DataQualityReport:
    """Structured result from OHLCV validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise ValueError("Invalid market data: " + "; ".join(self.errors))


def validate_ohlcv(
    df: pd.DataFrame,
    *,
    require_volume: bool = True,
    require_monotonic_index: bool = True,
    max_return_pct: float | None = 0.75,
) -> DataQualityReport:
    """Validate common structural and numerical OHLCV invariants."""
    errors: List[str] = []
    warnings: List[str] = []
    if df.empty:
        return DataQualityReport(False, ["DataFrame is empty"], warnings)
    required = REQUIRED_COLUMNS if require_volume else REQUIRED_COLUMNS[:-1]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return DataQualityReport(False, [f"Missing columns: {missing}"], warnings)
    if not isinstance(df.index, pd.DatetimeIndex):
        errors.append("Index must be a DatetimeIndex")
    else:
        if df.index.has_duplicates:
            errors.append("Index contains duplicate timestamps")
        if require_monotonic_index and not df.index.is_monotonic_increasing:
            errors.append("Index must be sorted in increasing order")
        if df.index.tz is None:
            warnings.append("DatetimeIndex is timezone-naive")
    numeric = df[list(required)].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        errors.append("Required OHLCV columns contain non-numeric or missing values")
    if not numeric.empty:
        if (numeric[["Open", "High", "Low", "Close"]] <= 0).any().any():
            errors.append("OHLC prices must be positive")
        if require_volume and (numeric["Volume"] < 0).any():
            errors.append("Volume cannot be negative")
        valid_ohlc = (
            (numeric["High"] >= numeric[["Open", "Close"]].max(axis=1))
            & (numeric["Low"] <= numeric[["Open", "Close"]].min(axis=1))
        )
        if not valid_ohlc.all():
            errors.append("OHLC relationship is invalid for at least one row")
        returns = numeric["Close"].pct_change().abs()
        if max_return_pct is not None and (returns > max_return_pct).any():
            warnings.append(
                f"Large absolute close-to-close return exceeds {max_return_pct:.0%}"
            )
    return DataQualityReport(not errors, errors, warnings)
