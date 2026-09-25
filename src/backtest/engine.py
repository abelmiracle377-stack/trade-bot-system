"""Vectorized + event-driven hybrid backtester."""

from typing import Dict, List, Optional, cast
import numpy as np
import pandas as pd
from loguru import logger
from dataclasses import dataclass, field
from .metrics import sortino_ratio, max_drawdown_duration, calmar_ratio


@dataclass
class Trade:
    symbol: str
    entry_date: pd.Timestamp
    exit_date: Optional[pd.Timestamp]
    side: int  # +1 long, -1 short
    entry_price: float
    exit_price: Optional[float]
    size: float  # dollar notional
    pnl: float = 0.0
    return_pct: float = 0.0


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[Trade]
    metrics: Dict[str, float | int]
    positions: pd.DataFrame = field(default_factory=pd.DataFrame)


class Backtester:
    """
    Simple multi-asset backtester.
    - Signals are already generated (daily)
    - Position sizing via RiskManager
    - Transaction costs + slippage applied
    - Stop-loss / take-profit checked daily
    """

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        risk_manager=None,
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.risk_manager = risk_manager

    def run(
        self,
        prices: Dict[str, pd.DataFrame],  # symbol → OHLCV
        signals: Dict[str, pd.Series],  # symbol → signal series (+1/0/-1)
        feature_vols: Optional[Dict[str, pd.Series]] = None,
    ) -> BacktestResult:
        """
        prices and signals must share a common DatetimeIndex (aligned).
        """
        # Align all series on common dates
        common_idx: pd.Index | None = None
        for s in signals.values():
            common_idx = s.index if common_idx is None else common_idx.intersection(s.index)
        if common_idx is None:
            raise ValueError("No signal data supplied for backtest")
        for df in prices.values():
            common_idx = common_idx.intersection(df.index)

        common_idx = common_idx.sort_values()
        if len(common_idx) < 10:
            raise ValueError("Insufficient overlapping data for backtest")

        symbols = list(signals.keys())
        close = {sym: prices[sym].loc[common_idx, "Close"] for sym in symbols}
        signal = {sym: signals[sym].loc[common_idx].fillna(0).astype(int) for sym in symbols}

        # Portfolio state
        cash = self.initial_capital
        positions: Dict[str, float] = {s: 0.0 for s in symbols}  # shares
        entry_prices: Dict[str, float] = {s: 0.0 for s in symbols}
        entry_dates: Dict[str, Optional[pd.Timestamp]] = {s: None for s in symbols}
        sides: Dict[str, int] = {s: 0 for s in symbols}

        equity = []
        trades: List[Trade] = []
        position_history = []

        for i, dt in enumerate(common_idx):
            # 1. Mark-to-market
            port_value = cash
            for sym in symbols:
                port_value += positions[sym] * close[sym].iloc[i]

            # 2. Check stops / take-profits
            for sym in symbols:
                if positions[sym] != 0 and self.risk_manager is not None:
                    hit = self.risk_manager.apply_stops(
                        entry_prices[sym], close[sym].iloc[i], sides[sym]
                    )
                    if hit:
                        # Close position
                        exit_price = close[sym].iloc[i] * (
                            1 - self.slippage_pct * np.sign(positions[sym])
                        )
                        proceeds = positions[sym] * exit_price
                        commission = abs(proceeds) * self.commission_pct
                        cash += proceeds - commission

                        trade = Trade(
                            symbol=sym,
                            entry_date=entry_dates[sym],
                            exit_date=dt,
                            side=sides[sym],
                            entry_price=entry_prices[sym],
                            exit_price=exit_price,
                            size=abs(positions[sym] * entry_prices[sym]),
                            pnl=proceeds - (positions[sym] * entry_prices[sym]) - commission,
                            return_pct=(exit_price / entry_prices[sym] - 1) * sides[sym],
                        )
                        trades.append(trade)

                        positions[sym] = 0.0
                        sides[sym] = 0
                        entry_prices[sym] = 0.0
                        entry_dates[sym] = None

            # 3. Desired signals → target positions
            for sym in symbols:
                desired_side = signal[sym].iloc[i]
                current_side = sides[sym]

                if desired_side == current_side:
                    continue

                # Close existing if any
                if current_side != 0:
                    exit_price = close[sym].iloc[i] * (
                        1 - self.slippage_pct * np.sign(positions[sym])
                    )
                    proceeds = positions[sym] * exit_price
                    commission = abs(proceeds) * self.commission_pct
                    cash += proceeds - commission

                    trade = Trade(
                        symbol=sym,
                        entry_date=entry_dates[sym],
                        exit_date=dt,
                        side=current_side,
                        entry_price=entry_prices[sym],
                        exit_price=exit_price,
                        size=abs(positions[sym] * entry_prices[sym]),
                        pnl=proceeds - (positions[sym] * entry_prices[sym]) - commission,
                        return_pct=(exit_price / entry_prices[sym] - 1) * current_side,
                    )
                    trades.append(trade)
                    positions[sym] = 0.0
                    sides[sym] = 0

                # Open new if desired
                if desired_side != 0:
                    # Simple equal-risk sizing (or volatility target if vols provided)
                    if feature_vols and sym in feature_vols:
                        vol = feature_vols[sym].loc[dt] if dt in feature_vols[sym].index else 0.2
                    else:
                        vol = 0.20  # fallback annualized vol

                    dollar_size = (
                        self.risk_manager.volatility_target_size(
                            asset_vol=vol, portfolio_value=port_value, signal=desired_side
                        )
                        if self.risk_manager
                        else (0.1 * port_value * desired_side)
                    )

                    if abs(dollar_size) < 100:  # min size filter
                        continue

                    entry_price = close[sym].iloc[i] * (
                        1 + self.slippage_pct * np.sign(dollar_size)
                    )
                    shares = dollar_size / entry_price
                    cost = abs(shares * entry_price)
                    commission = cost * self.commission_pct

                    if cost + commission > cash:
                        # Scale down to available cash
                        shares = (
                            (cash * 0.95)
                            / (entry_price * (1 + self.commission_pct))
                            * np.sign(dollar_size)
                        )
                        cost = abs(shares * entry_price)
                        commission = cost * self.commission_pct

                    # Long positions consume cash; short positions receive sale proceeds.
                    if desired_side > 0:
                        cash -= cost + commission
                    else:
                        cash += cost - commission

                    positions[sym] = shares
                    sides[sym] = desired_side
                    entry_prices[sym] = entry_price
                    entry_dates[sym] = dt

            # 4. Record equity
            port_value = cash
            for sym in symbols:
                port_value += positions[sym] * close[sym].iloc[i]
            equity.append({"date": dt, "equity": port_value, "cash": cash})

            pos_row = {"date": dt}
            for sym in symbols:
                pos_row[sym] = positions[sym]
            position_history.append(pos_row)

            # 5. Drawdown kill switch
            if self.risk_manager and i > 20:
                eq_series = pd.Series([e["equity"] for e in equity])
                if self.risk_manager.check_drawdown(eq_series):
                    logger.warning("Max drawdown hit – liquidating all positions")
                    for sym in symbols:
                        if positions[sym] != 0:
                            exit_price = close[sym].iloc[i]
                            proceeds = positions[sym] * exit_price
                            commission = abs(proceeds) * self.commission_pct
                            cash += proceeds - commission
                            positions[sym] = 0.0
                            sides[sym] = 0
                    break

        equity_df = pd.DataFrame(equity).set_index("date")["equity"]
        pos_df = pd.DataFrame(position_history).set_index("date")

        metrics = self._compute_metrics(equity_df, trades)
        return BacktestResult(
            equity_curve=equity_df,
            trades=trades,
            metrics=metrics,
            positions=pos_df,
        )

    def _compute_metrics(self, equity: pd.Series, trades: List[Trade]) -> Dict[str, float | int]:
        if equity.empty or len(equity) < 2:
            return {}

        rets = equity.pct_change().dropna()
        total_return = equity.iloc[-1] / equity.iloc[0] - 1
        years = (equity.index[-1] - equity.index[0]).days / 365.25
        cagr = (1 + total_return) ** (1 / max(years, 1e-6)) - 1 if years > 0 else 0.0
        vol = rets.std() * np.sqrt(252)
        sharpe = (cagr - 0.04) / vol if vol > 0 else 0.0

        peak = equity.cummax()
        dd = (equity - peak) / peak
        max_dd = dd.min()

        win_trades = [t for t in trades if t.pnl > 0]
        loss_trades = [t for t in trades if t.pnl <= 0]
        win_rate = len(win_trades) / len(trades) if trades else 0.0
        avg_win = np.mean([t.pnl for t in win_trades]) if win_trades else 0.0
        avg_loss = np.mean([t.pnl for t in loss_trades]) if loss_trades else 0.0
        profit_factor = (
            abs(sum(t.pnl for t in win_trades) / sum(t.pnl for t in loss_trades))
            if loss_trades and sum(t.pnl for t in loss_trades) != 0
            else np.inf
        )
        sortino = sortino_ratio(rets, risk_free_rate=0.04)
        calmar = calmar_ratio(cagr, max_dd)
        drawdown_duration = max_drawdown_duration(equity)

        return {
            "total_return": total_return,
            "cagr": cagr,
            "volatility": vol,
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": calmar,
            "max_drawdown": max_dd,
            "max_drawdown_duration": float(drawdown_duration),
            "n_trades": len(trades),
            "win_rate": win_rate,
            "avg_win": cast(float, avg_win),
            "avg_loss": cast(float, avg_loss),
            "profit_factor": profit_factor,
            "final_equity": float(equity.iloc[-1]),
        }
