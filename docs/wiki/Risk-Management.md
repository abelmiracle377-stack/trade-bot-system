# Risk Management

Risk controls are a critical part of the system. They protect the portfolio from excessive concentration, volatility spikes, and unsustainable drawdowns.

## Risk features

The project includes:

- maximum position percentage per asset
- overall leverage caps
- stop-loss logic
- take-profit logic
- drawdown limits
- volatility targeting
- position sizing via a fractional Kelly-inspired allocation approach

## Default configuration

From `config/config.yaml`:

```yaml
risk:
  max_position_pct: 0.15
  max_portfolio_leverage: 1.0
  stop_loss_pct: 0.08
  take_profit_pct: 0.20
  max_drawdown_pct: 0.25
  volatility_target: 0.12
  kelly_fraction: 0.25
```

## How position sizing works

The strategy combines the model signal with realized volatility to determine how much capital to allocate to each trade. This helps maintain a consistent risk budget across assets.

## Why it matters

Without risk controls, a signal model can produce large losses even if the directional predictions are statistically meaningful. Risk management is therefore just as important as the predictive model itself.

## Best practices

- start with conservative position limits
- avoid large portfolio leverage
- evaluate drawdown under realistic market stress
- paper-trade before deployment
- tune risk settings alongside model thresholds
