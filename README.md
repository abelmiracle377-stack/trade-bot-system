# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Abel Miracle

# AI Trading System

A modular, production-oriented **AI-powered quantitative trading system** written in Python.

It combines historical market data, rich technical feature engineering, machine-learning signal generation, volatility-targeted position sizing, stop-loss / take-profit rules, and a multi-asset backtester with realistic transaction costs.

> **Disclaimer**: This is research / educational software only.
> It is **not** financial advice. Past performance does not guarantee future results.
> Always paper-trade and fully understand the risks before using real capital.

---

## Fresh Clone – Install, Build, Test

The repository is designed so a new checkout can be installed, built, and tested without live market credentials.

~~~bash
git clone https://github.com/abelmiracle377-stack/trade-bot-system.git
cd trade-bot-system

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip check

# Build the source distribution and wheel
python -m build

# Run the complete test suite
python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=65
~~~

Equivalent Make targets:

~~~bash
make install-dev
make build
make test
~~~

The integration suite can be run independently:

~~~bash
make integration
# or
python -m pytest tests/integration/ -v
~~~

The full local CI sequence is:

~~~bash
make ci
~~~

It installs the pinned development environment, builds the package, runs lint/format checks, and runs the coverage-gated test suite.

### Run tests in an isolated container

~~~bash
docker compose run --rm test
# or
make docker-test
~~~

### Run the trading pipeline

~~~bash
python main.py
# or
make run
~~~

### Run the broker trading agent

The repository now includes a broker execution layer using Alpaca's official Python SDK. Alpaca supports paper trading with a separate paper environment, and its Trading API accepts market orders through the `/v2/orders` endpoint. The agent is deliberately **paper-first**.

Set credentials locally:

~~~bash
cp .env.example .env
# edit .env with your Alpaca paper credentials
export ALPACA_API_KEY="..."
export ALPACA_API_SECRET="..."
~~~

Run one paper-trading decision cycle:

~~~bash
python scripts/run_trading_agent.py
~~~

The agent:

1. Fetches and validates market data.
2. Engineers the same features used by the backtester.
3. Trains the configured chronological ML predictor.
4. Converts the latest probability into a long/flat/short signal.
5. Reads current broker equity and position state.
6. Applies deterministic daily-loss, drawdown, leverage, position-size, and data-age limits.
7. Submits a market order only when the risk gate allows it.

### Automated paper-trading agent

GitHub Actions can run the broker agent automatically on a weekday schedule in **paper-trading mode**. Configure these repository secrets:

- `ALPACA_PAPER_API_KEY`
- `ALPACA_PAPER_API_SECRET`

The workflow is `.github/workflows/trading-agent.yml`. It can also be started manually from the GitHub Actions tab.

The scheduled workflow explicitly sets `ALLOW_LIVE_TRADING=NO`, so it cannot enable live execution. It uploads the run logs and runtime risk state as short-lived GitHub Actions artifacts for inspection.

### Live trading

Live execution is **explicitly disabled by default**. To enable the live adapter, both conditions are required:

~~~bash
export ALLOW_LIVE_TRADING=YES
python scripts/run_trading_agent.py --live
~~~

Do not enable live trading until the strategy has been independently validated in paper trading. Live orders can lose real money, and model/backtest performance does not guarantee future results.

The agent uses Alpaca's live API only when `--live` is supplied and `ALLOW_LIVE_TRADING=YES`; otherwise it uses Alpaca's paper environment. Alpaca documents separate credentials/endpoints for paper and live trading.


~~~bash
python main.py
# or
make run
~~~

---

## Architecture

The system is organized as independent layers so market-data handling, feature engineering, machine-learning models, risk controls, and backtesting can be tested separately and together.

- `src/data/` validates, fetches, caches, and aligns market data.
- `src/features/` transforms OHLCV data into technical and statistical features.
- `src/models/` trains chronological ML predictors and produces probabilities.
- `src/strategies/` converts model outputs into trading signals.
- `src/risk/` contains position sizing, stops, drawdown controls, and deterministic hard limits.
- `src/backtest/` simulates multi-asset positions and calculates performance metrics.
- `tests/integration/` verifies that these layers work together using deterministic local fixtures.

The integration path is intentionally reproducible:

~~~text
OHLCV fixture
    -> validation
    -> feature engineering
    -> chronological model training
    -> probabilities/signals
    -> backtest
    -> equity + metrics
~~~

---

## What the Test Suite Covers

| Area | Coverage |
|---|---|
| Data quality | OHLCV structure, timestamps, numerical constraints |
| Data fetching | Fetching and caching with mocked provider behavior |
| Features | Technical indicators and engineered returns |
| Models | ML fit/predict, persistence, and chronological validation |
| Leakage | Forward-return target and feature-leakage regressions |
| Risk | Position sizing, stops, drawdown, hard limits, stale data |
| Backtesting | Portfolio accounting, long/short positions, metrics |
| Walk-forward | Chronological splits and embargo |
| Integration | Data → features → model → signals → backtest |
| Baselines | Comparison against naive strategies |

All tests use deterministic fixtures or mocks and do not require brokerage credentials or live orders.

---

## Project Structure

~~~text
ai_trading_system/
├── .github/workflows/ci.yml      # Lint + type + test + security on every push
├── config/config.yaml
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── strategies/
│   ├── risk/
│   ├── backtest/
│   ├── portfolio/
│   └── utils/
├── tests/
│   ├── integration/              # Cross-component deterministic tests
│   └── ...
├── main.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pytest.ini
├── requirements.txt              # Pinned runtime dependencies
├── requirements-dev.txt          # Pinned development tooling
├── requirements-lock.txt         # Reproducible runtime + development pins
├── pyproject.toml                # Build/package metadata
├── .env.example
├── SECURITY.md
├── CONTRIBUTING.md
└── README.md
~~~

---

## Development Commands

~~~bash
make help
make install-dev
make build
make test
make integration
make lint
make format
make ci
make docker-test
make docker-run
~~~

---

## Configuration

Edit `config/config.yaml` for symbols, model type, risk limits, validation settings, and backtest parameters.

Copy `.env.example` to `.env` only when environment overrides are needed. Never commit real credentials.

---

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request:

- Multi-Python matrix (3.10 / 3.11 / 3.12)
- Dependency installation and `pip check`
- Python package build
- Ruff lint + format check
- mypy type checking
- Full pytest suite with a 65% coverage gate
- Bandit security scan
- pip-audit dependency scan

The repository also uses CodeQL and Dependabot for additional security and dependency maintenance.

---

## Extending

- New model → implement `fit` / `predict_proba` / `save` / `load` in `src/models/`
- Change prediction target → edit `_create_target` in `SignalPredictor`
- Walk-forward validation → use `src/utils/walk_forward.py` with an embargo for forward-return labels
- Market-data quality → validate OHLCV before caching with `src/data/validation.py`
- Hard risk controls → use `src/risk/limits.py` as a deterministic gate before orders
- Live trading → replace the backtester with a broker connector and keep deterministic risk controls in front of any model recommendation

---

## License

This project is licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for the complete license text and [NOTICE](NOTICE) for attribution information.

The package metadata also declares Apache-2.0 so tooling and package indexes can identify the license consistently.

---

## Experiment Tracking & Reproducibility

Run a fully tracked experiment:

~~~bash
python scripts/run_experiment.py --config config/config.yaml
python scripts/run_experiment.py --config config/config.yaml --run-id my_exp_001
~~~

Results are appended to `reports/experiment_log.jsonl` and a per-run summary is written to `reports/<run_id>_summary.json`.

All runs are seeded via `config.yaml` → `model.random_state` for reproducibility.

## Research Integrity Safeguards

The system includes chronological walk-forward split utilities with an optional embargo, OHLCV data-quality validation before caching, forward-target leakage regression tests, risk-adjusted backtest metrics, and deterministic hard risk limits separate from model logic.
