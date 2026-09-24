# AI Trading System

A modular, production-oriented **AI-powered quantitative trading system** written in Python.

> **Disclaimer:** This is research and educational software only. It is **not financial advice**. Past performance does not guarantee future results. Always paper-trade and understand the risks before using real capital.

## License

This project is licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for the complete license text and [`NOTICE`](NOTICE) for attribution information.

The Apache License 2.0 permits commercial and private use, modification, distribution, and patent use, subject to its conditions. In particular, redistributions must include a copy of the license and preserve applicable notices. Contributions are accepted under the terms described in [`CONTRIBUTING.md`](CONTRIBUTING.md).

The repository's Python package metadata, GitHub license detection, and documentation intentionally identify the same license: `Apache-2.0`.

## Quick start

```bash
git clone https://github.com/abelmiracle377-stack/trade-bot-system.git
cd trade-bot-system

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/ -v --cov=src --cov-report=term-missing
```

Run the pipeline with:

```bash
python main.py
# or
make run
```

All tests are designed to run without network access or external credentials.

## Project structure

```text
.github/workflows/   CI and dependency automation
config/              YAML configuration
src/                 data, features, models, strategies, risk, and backtesting
tests/               pytest suite
scripts/             experiment tooling
main.py              end-to-end pipeline
```

## Development

```bash
make install-dev
make test
make lint
make format
make ci
make docker-test
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development conventions. Do not commit secrets, generated models, market-data caches, reports, or logs. Use [`.env.example`](.env.example) as the template for local environment variables.

## Security

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and security practices. This project does not place live orders by default; any live-trading integration requires a separate security review.

## Reproducible experiments

```bash
python scripts/run_experiment.py --config config/config.yaml
python scripts/run_experiment.py --config config/config.yaml --run-id my_exp_001
```

Pinned dependencies are available in [`requirements-lock.txt`](requirements-lock.txt). Experiment outputs are written to the ignored `reports/` directory.
