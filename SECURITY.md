# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security issue, please open a private security advisory on GitHub or email the maintainer. Do not open a public issue for vulnerabilities.

## Security Practices in This Project

- **No hardcoded secrets** – API keys and credentials must be supplied via environment variables (see `.env.example`).
- **Dependency scanning** – CI runs `bandit` and `safety` on every push.
- **Non-root Docker** – The production image runs as an unprivileged user.
- **Input handling** – Configuration is loaded from YAML; runtime market data is treated as untrusted input and sanitized by the data layer.
- **Logging** – Structured logging is available; sensitive values should never be logged.

## Threat Model (Research System)

This is a **research / backtesting** system. It does not place live orders by default. The main risks are:

1. Accidental exposure of future broker API keys if live trading is later added.
2. Supply-chain risk from third-party packages (mitigated by pinned requirements + lockfile + CI audits).
3. Local data / model poisoning if an attacker can write to the cache or models directories.

When adding live trading, treat broker credentials as high-value secrets and enforce least-privilege API keys.
