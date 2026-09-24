# Getting Started

This page covers the steps to install, run, and validate the project locally.

## 1. Clone the repository

```bash
git clone https://github.com/abelmiracle377-stack/trade-bot-system.git
cd trade-bot-system
```

## 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 4. Run the test suite

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Alternative:

```bash
make test
```

## 5. Run the trading pipeline

```bash
python main.py
```

Or:

```bash
make run
```

## 6. Use Docker (optional)

```bash
docker compose run --rm test
```

## Recommended workflow

1. Review `config/config.yaml`
2. Confirm the symbols, time range, and model settings
3. Run the pipeline in dry-run or research mode
4. Validate the output metrics and equity curve
5. Only then consider live deployment or extended experiments

## Environment variables

Copy the sample file if you later add a broker or exchange integration:

```bash
cp .env.example .env
```

Do not commit secrets to the repository.
