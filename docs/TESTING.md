# Testing Guide

The test suite covers core data, feature-engineering, model, signal, risk,
portfolio, and backtesting behavior. Add regression tests for every material
behavior change.

For this trading system, important failure-path scenarios include:

- missing or stale market data;
- malformed external API responses;
- unavailable data providers;
- invalid configuration;
- oversized or invalid positions;
- duplicate or replayed order requests;
- insufficient capital;
- model persistence failures;
- broker/API timeouts and rate limits;
- drawdown and risk-limit breaches.

## Integration tests

Integration tests exercise multiple trading-system layers together using
deterministic local fixtures. They do not call Yahoo Finance, require API
credentials, or place orders.

Run them with:

```bash
pytest tests/integration/ -v
```

The main pipeline test covers:

```text
OHLCV fixture
    -> data-quality validation
    -> technical feature engineering
    -> chronological ML training
    -> model probabilities
    -> trading signals
    -> backtest engine
    -> equity and performance metrics
```

This keeps the integration suite reproducible on a fresh checkout while still
checking that the major components can work together.

Tests should use deterministic fixtures and mocked external services. They
must never require real brokerage credentials or place real orders.
