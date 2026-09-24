# Configuration

The project configuration is stored in `config/config.yaml`.

## Overview

The YAML file controls the following sections:

- `data`
- `features`
- `model`
- `strategy`
- `risk`
- `backtest`
- `logging`

## Example config

```yaml
data:
  symbols:
    - AAPL
    - MSFT
    - GOOGL
    - AMZN
    - NVDA
  start_date: "2018-01-01"
  end_date: null
  interval: "1d"
  cache_dir: "data/cache"

features:
  lookback_windows: [5, 10, 20, 50]
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bb_period: 20
  bb_std: 2.0
  atr_period: 14
  volume_ma_period: 20

model:
  type: "xgboost"
  target_horizon: 5
  train_test_split: 0.8
  random_state: 42
```

## Important settings

### Data

- `symbols`: assets to analyze
- `start_date`: first date used for historical data
- `end_date`: optional upper date bound
- `interval`: candle frequency (for example, `1d`)

### Strategy

- `signal_threshold`: long entry threshold
- `short_threshold`: short threshold
- `allow_short`: enables short-side logic

### Risk

- `max_position_pct`: maximum per-asset portfolio weight
- `max_portfolio_leverage`: maximum overall leverage
- `stop_loss_pct`: stop-loss threshold
- `take_profit_pct`: take-profit threshold
- `max_drawdown_pct`: maximum acceptable portfolio drawdown
- `volatility_target`: target volatility level

### Backtest

- `initial_capital`: starting portfolio value
- `commission_pct`: transaction cost
- `slippage_pct`: estimate for execution friction

## Editing

Update the file and rerun the pipeline to test the effect of the new settings:

```bash
python main.py
```

## Security note

Never commit API keys or brokerage credentials. Use `.env` files only locally and keep them out of source control.
