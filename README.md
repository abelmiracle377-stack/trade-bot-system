# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Abel Miracle

# AI Trading System

A modular, production-oriented **AI-powered quantitative trading system** written in Python.

It combines historical market data, rich technical feature engineering, machine-learning signal generation, volatility-targeted position sizing, stop-loss / take-profit rules, and a multi-asset backtester with realistic transaction costs.

> **Disclaimer**: This is research / educational software only.  
> It is **not** financial advice. Past performance does not guarantee future results.  
> Always paper-trade and fully understand the risks before using real capital.

---

## Fresh Clone – Exact Commands Buyers Run

```bash
git clone <repo-url> ai_trading_system
cd ai_trading_system

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

# THIS IS THE CRITICAL COMMAND – must succeed
pytest tests/ -v --cov=src --cov-report=term-missing

# Alternative
make test
```

### Run tests in a completely isolated container
```bash
docker compose run --rm test
# or
make docker-test
```

### Run the trading pipeline
```bash
python main.py
# or
make run
```

---

## What the Test Suite Covers

| File                        | What it tests                              |
|-----------------------------|--------------------------------------------|
| `tests/test_smoke.py`       | Imports, config loading, basic objects     |
| `tests/test_data_fetcher.py`| Data fetching + caching (mocked)           |
| `tests/test_features.py`    | Technical feature engineering              |
| `tests/test_predictor.py`   | ML model fit / predict / save / load       |
| `tests/test_signal.py`      | Signal generation from probabilities       |
| `tests/test_risk.py`        | Position sizing, stops, drawdown checks    |
| `tests/test_backtest.py`    | Full backtest engine + metrics             |
| `tests/test_data_quality.py`| OHLCV structural and numerical validation  |
| `tests/test_walk_forward.py`| Chronological splits + embargo              |
| `tests/test_metrics.py`     | Sortino, Calmar, drawdown duration          |
| `tests/test_risk_limits.py` | Deterministic hard risk limits              |
| `tests/test_model_leakage.py`| Forward-target leakage regression checks   |

All tests run **without network access** or external credentials.

---

## Project Structure

```
ai_trading_system/
├── .github/workflows/ci.yml      # Lint + type + test on every push
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
├── tests/                        # Full pytest suite
├── main.py
├── Dockerfile                    # Multi-stage (production + test)
├── docker-compose.yml
├── Makefile
├── pytest.ini
├── requirements.txt              # Pinned runtime
├── requirements-dev.txt
├── requirements-lock.txt
├── pyproject.toml
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---

## Development Commands

```bash
make help
make install-dev
make test
make lint
make format
make ci                 # full local CI
make docker-test        # tests inside Docker
make docker-run         # pipeline inside Docker
```

---

## Configuration

Edit `config/config.yaml` for symbols, model type, risk limits, etc.

Copy `.env.example` → `.env` only if you later add live broker keys (never commit secrets).

---

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request:

- Multi-Python matrix (3.10 / 3.11 / 3.12)
- Ruff lint + format check
- Full pytest suite with coverage
- Bandit + pip-audit security scans

---

## Extending

- New model → implement `fit` / `predict_proba` / `save` / `load` in `src/models/`
- Change prediction target → edit `_create_target` in `SignalPredictor`
- Walk-forward validation → use `src/utils/walk_forward.py` with an embargo for forward-return labels
- Market-data quality → validate OHLCV before caching with `src/data/validation.py`
- Hard risk controls → use `src/risk/limits.py` as a deterministic gate before orders
- Live trading → replace backtester with a broker connector and keep deterministic risk controls in front of any model recommendation

---

## License

This project is licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for the complete license text and [NOTICE](NOTICE) for attribution information.

The package metadata also declares Apache-2.0 so tooling and package indexes can identify the license consistently.

---

## Experiment Tracking & Reproducibility

Run a fully tracked experiment (logs parameters, model metrics, and backtest results):

```bash
python scripts/run_experiment.py --config config/config.yaml
python scripts/run_experiment.py --config config/config.yaml --run-id my_exp_001
```

Results are appended to `reports/experiment_log.jsonl` and a per-run summary is written to `reports/<run_id>_summary.json`.

Baseline comparison tests live in `tests/test_model_baseline.py` and verify the ML model outperforms naive strategies (always-long and moving-average crossover) on synthetic data.

All runs are seeded via `config.yaml` → `model.random_state` for reproducibility.

### Exact reproducible install

```bash
pip install -r requirements-lock.txt
```

## Research Integrity Safeguards

The system now includes chronological walk-forward split utilities with an optional embargo, OHLCV data-quality validation before caching, forward-target leakage regression tests, and additional risk-adjusted backtest metrics. Hard risk limits are represented separately from model logic so a model recommendation cannot override deterministic safety checks.
