"""Tests for SignalGenerator."""

import pandas as pd
import numpy as np
from src.strategies.signal import SignalGenerator


def test_long_only_signals():
    proba = pd.Series([0.4, 0.6, 0.7, 0.3, 0.55], index=pd.date_range("2023-01-01", periods=5))
    gen = SignalGenerator(long_threshold=0.55, allow_short=False)
    signals = gen.generate(proba)

    assert list(signals) == [0, 1, 1, 0, 1]
    assert (signals >= 0).all()


def test_with_shorts():
    proba = pd.Series([0.3, 0.6, 0.2, 0.8], index=pd.date_range("2023-01-01", periods=4))
    gen = SignalGenerator(long_threshold=0.55, short_threshold=0.40, allow_short=True)
    signals = gen.generate(proba)

    assert list(signals) == [-1, 1, -1, 1]


def test_all_flat():
    proba = pd.Series([0.5] * 10)
    gen = SignalGenerator(long_threshold=0.6, short_threshold=0.4, allow_short=True)
    signals = gen.generate(proba)
    assert (signals == 0).all()
