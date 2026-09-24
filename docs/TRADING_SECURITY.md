# Trading Security Boundaries

This repository is a research/backtesting system and does not place live
orders by default. Any future live-trading integration must preserve the
deterministic risk controls around model outputs.

## Threats

- exposed API or brokerage credentials;
- stale, malformed, or manipulated market data;
- duplicate or replayed orders;
- oversized orders or excessive leverage;
- broker/API outage and rate-limit failures;
- unsafe automation influenced by AI-generated recommendations;
- local cache/model poisoning.

## Required safeguards for live trading

Use least-privilege credentials, explicit position and loss limits, paper or
dry-run mode during validation, idempotent order handling where supported,
timeouts with bounded retries, audit logging, and a manual/automated kill
switch.

AI-generated recommendations must not bypass deterministic risk controls.
Secrets must never appear in prompts, logs, fixtures, or source control.
