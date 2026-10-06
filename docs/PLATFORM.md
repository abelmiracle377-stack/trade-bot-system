# TradeAI Platform

TradeAI is the web product layer for the AI Trading System.

## Product modules

- Authentication and account management
- Demo/paper trading
- Broker/exchange connection
- AI market analysis
- Signal sharing
- Portfolio analytics
- Subscription tiers
- Risk-controlled automated execution

## Execution safety

The AI does not bypass the deterministic execution layer. Real-money execution remains disabled unless the broker is connected and the explicit live-trading approval gate is satisfied.

Protective exits are independent of the AI model. The repository includes `scripts/protect_live_trades.py`, which can close a position when its configured hard loss threshold is reached.

## Current integration boundary

The existing Python engine supports Alpaca paper/live execution and risk checks. The `web/` directory is the product UI. Production authentication/database and billing still need a server-side service before real user credentials or payments are accepted.

Never collect broker API secrets directly in browser JavaScript. Never put payment secrets in frontend code.
