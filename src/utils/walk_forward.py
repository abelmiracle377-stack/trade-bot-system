"""Leakage-resistant time-series walk-forward splitting."""

from dataclasses import dataclass
from typing import Iterator
import pandas as pd

@dataclass(frozen=True)
class WalkForwardSplit:
    train: pd.Index
    test: pd.Index

def walk_forward_splits(
    index: pd.Index,
    *,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
    embargo: int = 0,
) -> Iterator[WalkForwardSplit]:
    """Yield expanding-window train/test splits in chronological order.

    embargo leaves observations immediately before each test window out of
    training, reducing target-overlap leakage for forward-return labels.
    """
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    if embargo < 0:
        raise ValueError("embargo must be non-negative")
    step = step_size or test_size
    if step <= 0:
        raise ValueError("step_size must be positive")
    if not index.is_monotonic_increasing:
        raise ValueError("index must be sorted chronologically")
    if index.has_duplicates:
        raise ValueError("index must not contain duplicates")
    n = len(index)
    train_end = train_size
    while train_end + embargo + test_size <= n:
        test_start = train_end + embargo
        yield WalkForwardSplit(
            train=index[:train_end],
            test=index[test_start:test_start + test_size],
        )
        train_end += step
