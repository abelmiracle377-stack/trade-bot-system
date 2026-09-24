# Backtesting

Backtesting is how the project tests a strategy using historical market data.

## What is backtested

The backtest engine evaluates:

- signal generation
- trade entries and exits
- risk enforcement
- portfolio allocation
- realized performance metrics

## Execution flow

When the pipeline runs, it does the following:

1. loads historical price data
2. builds features
3. trains the model
4. produces model probabilities
5. converts probabilities into position signals
6. sizes trades using the configured risk model
7. executes the simulated portfolio strategy
8. calculates summary metrics

## Outputs

The pipeline writes reports to the `reports/` directory, including:

- equity curve image
- trade summary CSV
- performance metrics in logs

## Example metrics

Typical outputs include:

- total return
- annualized return
- volatility
- Sharpe ratio
- max drawdown
- win rate
- average trade return

## Running a backtest

```bash
python main.py
```

The system will save:

- `reports/equity_curve.png`
- `reports/trades.csv`

## Notes

Backtests are useful for research, but they do not guarantee future performance. Use them as a decision tool, not a promise of profitability.
