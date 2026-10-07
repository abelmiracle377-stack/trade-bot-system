# TradeAI API

The API is intentionally split into small boundaries so the browser never talks directly to a broker.

- `GET /api/health` — service status.
- `GET /api/markets` — supported market universe.
- `GET /api/auth` — managed-auth configuration status.
- `GET /api/account` — demo/paper account snapshot.
- `POST /api/risk/check` — deterministic risk decision.
- `POST /api/orders/paper` — paper-order validation boundary.

## Execution policy

Paper trading is the default. The API does not accept broker secrets, does not enable live execution, and does not allow an AI response to bypass risk controls.

Production account persistence, managed authentication, billing, broker OAuth/API connections and live execution require server-side provider configuration. Live execution must remain separately approved and gated.
