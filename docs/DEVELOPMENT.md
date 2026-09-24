# Development Guide

## Setup

Create and activate a virtual environment, then install the pinned runtime and development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Quality checks

Run the same checks used by CI before opening a pull request:

```bash
make ci
pre-commit run --all-files
```

## Tests

Run the complete suite with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

The tests are designed to run without live brokerage credentials or network access.

## Configuration

Use `.env.example` for non-sensitive configuration documentation. Never commit
real API keys, brokerage credentials, passwords, tokens, or private certificates.

## Pull requests

Keep changes focused. Add or update tests when behavior changes, and document
security-sensitive changes in the pull request.
