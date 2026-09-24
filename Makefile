lint:
	ruff check src/ tests/ main.py scripts/
	ruff format --check src/ tests/ main.py scripts/

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=65

format:
	ruff format src/ tests/ main.py scripts/
	ruff check --fix src/ tests/ main.py scripts/

check: lint test

ci: install-dev lint test
