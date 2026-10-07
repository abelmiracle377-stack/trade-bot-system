# Production API and environment setup

The website can run in paper/demo mode without external credentials. Real broker execution, managed user accounts, persistence, and billing require server-side provider configuration.

## Required for Alpaca paper trading

Add these as **Vercel environment variables** (never put them in `web/index.html`, GitHub source, or browser localStorage):

- `TRADING_API_TOKEN` — private server-to-server token for the current broker API boundary.
- `ALPACA_PAPER_API_KEY` — Alpaca paper trading key.
- `ALPACA_PAPER_API_SECRET` — Alpaca paper trading secret.

For compatibility with the existing trading engine, `ALPACA_API_KEY` and `ALPACA_API_SECRET` may also be used for paper mode.

## Required before live trading

Live trading is intentionally disabled unless all of these are configured server-side:

- `ALPACA_LIVE_API_KEY`
- `ALPACA_LIVE_API_SECRET`
- `ALLOW_LIVE_TRADING=YES`
- `LIVE_TRADING_APPROVED=YES`

The browser cannot enable the live gates.

## Production user accounts and persistence

A managed authentication provider and PostgreSQL-compatible database are still required for multi-user production accounts:

- `AUTH_PROVIDER`
- `DATABASE_URL`

The existing `docs/schema.sql` defines users, subscriptions, broker connections, orders, positions, and audit logs.

## Billing

A payment provider is required before paid plans can actually charge customers. Stripe is the intended integration, but no payment credentials are hard-coded or assumed. When billing is enabled, use server-side variables such as:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

## Market data

The public website currently uses Binance public market data for the visible crypto quotes. No private Binance API key is needed for those public quotes.

Stock/portfolio broker data should come from the authenticated broker/server boundary rather than exposing broker credentials to the browser.

## What is implemented now

- `/api/broker` — protected Alpaca configuration/status
- `/api/broker/account` — broker account snapshot
- `/api/broker/positions` — broker positions
- `/api/broker/orders` — market-order endpoint with paper default and live safety gates
- Existing `/api/orders/paper` remains a simulated/demo endpoint.

All broker endpoints require:

`Authorization: Bearer <TRADING_API_TOKEN>`

This is an interim server-side protection layer. It should be replaced/augmented by per-user managed authentication before exposing broker actions to arbitrary customers.
