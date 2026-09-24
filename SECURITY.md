# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security issue, please use a private GitHub security advisory or contact the maintainer privately. Do not open a public issue for an undisclosed vulnerability.

Please include the affected version/commit, affected component, reproduction steps, and the potential impact. Do not include real API keys, credentials, personal data, or other secrets in a report.

## Threat Model

This project is primarily a research and backtesting system. It does not place live orders by default. Its security boundary is therefore different from that of a deployed brokerage service.

### What this project protects

- Market-data inputs are validated before they are cached and consumed.
- Deterministic risk limits can block actions based on loss, drawdown, leverage, position size, and stale data.
- CI performs static security analysis with Bandit and dependency auditing with pip-audit.
- Runtime credentials are expected to come from environment/configuration rather than committed source files.
- Docker production images run as an unprivileged user.

### What this project does not protect automatically

- It does not guarantee that third-party market data is truthful or free from manipulation.
- It does not protect a host whose filesystem permissions allow an attacker to replace cached data or trusted model artifacts.
- It does not secure broker accounts or API credentials if live trading integrations are added.
- It does not make a trading strategy profitable or eliminate market, execution, or financial risk.

## Model Artifact Trust

Model persistence uses joblib. Joblib deserialization can execute arbitrary code if an attacker controls the model file. Only load model artifacts produced by a trusted pipeline and stored in a trusted location. Do not load untrusted `.joblib` files.

## Secrets

Never commit real secrets. `.env` is ignored by Git and `.env.example` contains placeholders only. If live broker support is added, use least-privilege API keys, restrict network access where possible, and rotate credentials after suspected exposure.

## Data and Input Security

Market data should be treated as untrusted input. Validate timestamps, OHLC relationships, missing values, numeric ranges, and freshness before using data in models or trading decisions.

## Reporting and Response

Security fixes should be developed privately when disclosure could expose an exploitable vulnerability. After a fix is available, update the changelog and communicate affected versions and mitigations as appropriate.
