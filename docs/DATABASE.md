# TradeAI persistence

Production persistence is designed for PostgreSQL via the `DATABASE_URL` server environment variable.

The browser demo uses local browser storage so paper orders and the demo account remain usable between page refreshes without pretending they are a real brokerage account.

Production user accounts, orders, positions, subscriptions and broker connections must be persisted server-side after managed authentication and PostgreSQL are configured.

Never store broker API secrets or payment secrets in browser storage.
