# Contributing

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Running Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
# or
make test
```

Tests must pass before any PR is merged. CI enforces this automatically.

## Code Style

We use `ruff` for linting and formatting:

```bash
make format
make lint
```

## Commit Style

Prefer small, focused commits:

- One logical change per commit
- Include tests that prove the new behavior in the same commit when possible
- Avoid mixing formatting, refactors, and features in a single commit

## Docker

To verify the project runs in isolation:

```bash
make docker-test
```
