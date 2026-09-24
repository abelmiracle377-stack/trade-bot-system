# Home

Welcome to the AI Trading System wiki.

This project is a modular Python-based trading system that combines:

- market data acquisition
- feature engineering
- machine learning signal generation
- risk management
- position sizing
- backtesting and reporting

## What this system does

The pipeline loads configuration, downloads historical market data, engineers technical indicators, trains a predictive model, generates buy/hold/sell signals, applies portfolio risk constraints, and runs a backtest to estimate strategy performance.

## Repository layout

```text
.
├── config/
│   └── config.yaml
├── src/
│   ├── backtest/
│   ├── data/
│   ├── features/
│   ├── portfolio/
│   ├── risk/
│   ├── strategies/
│   └── utils/
├── tests/
├── main.py
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .env.example
```

## Quick links

- [Getting Started](./Getting-Started.md)
- [Architecture](./Architecture.md)
- [Configuration](./Configuration.md)
- [Risk Management](./Risk-Management.md)
- [Backtesting](./Backtesting.md)
- [Troubleshooting](./Troubleshooting.md)

## Important note

This project is for research and educational use only. It is not financial advice. Always paper-trade before using any live capital.
