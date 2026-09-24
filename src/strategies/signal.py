"""Signal generation from model probabilities."""

import pandas as pd
from loguru import logger


class SignalGenerator:
    """Convert model probabilities into discrete trading signals."""

    def __init__(
        self,
        long_threshold: float = 0.55,
        short_threshold: float = 0.45,
        allow_short: bool = False,
    ):
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.allow_short = allow_short

    def generate(self, proba: pd.Series) -> pd.Series:
        """
        Returns signal series:
          +1 = long
           0 = flat / hold
          -1 = short (only if allow_short=True)
        """
        signal = pd.Series(0, index=proba.index, dtype=int)

        signal[proba >= self.long_threshold] = 1
        if self.allow_short:
            signal[proba <= self.short_threshold] = -1

        n_long = (signal == 1).sum()
        n_short = (signal == -1).sum()
        logger.debug(f"Signals generated → Long: {n_long}, Short: {n_short}, Flat: {(signal == 0).sum()}")
        return signal
