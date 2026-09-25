# Telegram Multi-User Trading Architecture

This document describes the additive Telegram and multi-user foundation. It does not replace the existing trading agent or broker execution layer.

## Current scope

The new foundation provides:

- Telegram-user-to-internal-user authorization
- Per-user trading permission metadata
- Broker-account identifiers without storing broker secrets
- Append-only signal/outcome records for future model learning
- A framework-neutral Telegram command boundary

The optional Telegram dependency is isolated in requirements-telegram.txt so the existing core runtime and CI are not changed by this feature until a deployment is explicitly enabled.

## Learning loop

Signals should be recorded first and labeled after their outcomes are known. Candidate model updates should then be evaluated with the existing chronological validation and backtesting controls before promotion. The system should never silently replace a live model because of a single new trade result.

## Live execution boundary

Live execution requires an authorized broker-account service and a per-user risk profile. Telegram commands must authenticate the user, validate the requested action, pass through the existing risk controls, and require explicit confirmation for consequential live orders.

Broker API keys and Telegram bot tokens must remain deployment secrets and must never be committed to Git.

## Next implementation stages

1. Connect Telegram Bot API using the optional dependency.
2. Add persistent user/account storage.
3. Add broker account authorization per user.
4. Add per-user risk profiles and limits.
5. Connect read-only account/position commands.
6. Add paper-trading commands and confirmation flows.
7. Add signal/outcome ingestion and model evaluation.
8. Enable live execution only after account authorization, risk controls, and deployment checks are complete.
