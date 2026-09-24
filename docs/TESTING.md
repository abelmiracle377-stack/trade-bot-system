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

Tests should use deterministic fixtures and mocked external services. They
must never require real brokerage credentials or place real orders.
