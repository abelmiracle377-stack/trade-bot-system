# Architecture

The trading system is built around a modular pipeline that transforms raw financial data into actionable trading decisions.

## High-level flow

```text
Market Data
   ↓
Feature Engineering
   ↓
ML Prediction Model
   ↓
Signal Generation
   ↓
Risk Management + Position Sizing
   ↓
Backtest + Metrics
   ↓
Reports / Equity Curve
```

## Main components

### Data layer

The `src/data` module is responsible for fetching and caching market data. The configuration file defines the symbols, date range, interval, and cache directory.

### Feature engineering

The `src/features` module creates technical indicators such as RSI, MACD, Bollinger Bands, ATR, and volume-based signals. These features are used to train a prediction model.

### Model layer

The `src/models` component trains a signal predictor. The model estimates the probability of future directional movement over a configured horizon.

### Strategy layer

The `src/strategies` module converts probabilities into trade signals such as long/neutral/short decisions based on threshold values.

### Risk and portfolio layer

The `src/risk` and `src/portfolio` modules enforce portfolio constraints, drawdown limits, volatility targets, and position sizing rules.

### Backtest engine

The `src/backtest` module runs a historical simulation using the generated signals and the defined risk policy. It outputs metrics such as return, Sharpe ratio, drawdown, and trade summaries.

## Entry point

The `main.py` script orchestrates the pipeline:

1. load configuration
2. fetch data
3. engineer features
4. train the model
5. generate signals
6. run risk-based backtest
7. save plots and reports

## Design principles

- modular component design
- configurable strategy parameters
- reproducible experiments
- safety-first risk controls
- clean separation between research and execution logic
