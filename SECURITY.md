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

This project is primarily a research and paper-trading system. Live order submission is a separate, explicit path. The main trust boundaries are the source repository, CI runner, runtime filesystem, market-data providers, and Alpaca broker credentials/API.

### Trust boundaries and failure modes

| Boundary | Protected asset | Threat | Mitigation | Residual risk |
|---|---|---|---|---|
| GitHub repository → CI runner | Source code and workflow configuration | Malicious dependency or workflow change | Read-only checkout, pinned dependencies, Ruff, mypy, Bandit, pip-audit, CodeQL | Repository compromise can still alter trusted automation |
| CI secret store → agent | Alpaca API credentials | Credential disclosure or misuse | Secrets are injected through GitHub Actions; no credentials in source; paper mode sets ALLOW_LIVE_TRADING=NO | A compromised runner/workflow could still access injected secrets |
| Runtime → broker | Order authority | Accidental or unauthorized live orders | Paper-first default, --live plus ALLOW_LIVE_TRADING=YES, deterministic loss/drawdown/leverage/size/freshness gates | Live mode remains financially consequential if explicitly enabled |
| Market data → model/risk engine | Trading decisions | Corrupt, stale, malformed, or manipulated data | OHLCV validation, freshness checks, cached-data validation | Validation cannot establish that an external feed is truthful |
| Runtime filesystem → model artifacts | Model integrity | Untrusted joblib/model replacement | Trusted-artifact guidance and restricted deployment assumptions | Filesystem compromise can defeat application-level trust |

The threat model is intentionally explicit about residual risk: these controls reduce accidental or common failure modes but do not make live trading risk-free.

### Primary mitigations

- Paper trading is the default execution mode.
- Live trading requires both --live and ALLOW_LIVE_TRADING=YES.
- Risk limits gate loss, drawdown, leverage, position size, order notional, and stale data.
- Broker credentials are read from environment variables rather than source files.
- Security scans run in CI with Bandit, pip-audit, and CodeQL.

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
