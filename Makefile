.PHONY: install install-dev build test integration lint format check ci clean run docker-build docker-test docker-run help

help:
	@echo "Available targets:"
	@echo "  install       Install runtime dependencies"
	@echo "  install-dev   Install runtime + development dependencies"
	@echo "  build         Build the Python source distribution and wheel"
	@echo "  test          Run the full test suite with coverage"
	@echo "  integration   Run integration tests"
	@echo "  lint          Run ruff linter"
	@echo "  format        Auto-format code with ruff"
	@echo "  check         lint + test"
	@echo "  ci            Full local CI simulation"
	@echo "  run           Execute the trading pipeline"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-test   Run tests inside Docker (isolated)"
	@echo "  docker-run    Run the pipeline inside Docker"
	@echo "  clean         Remove caches and temporary files"

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-lock.txt
	python -m pip check

build:
	python -m build

test:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=65

integration:
	python -m pytest tests/integration/ -v

lint:
	ruff check src/ tests/ main.py scripts/
	ruff format --check src/ tests/ main.py scripts/

format:
	ruff format src/ tests/ main.py scripts/
	ruff check --fix src/ tests/ main.py scripts/

check: lint test

ci: install-dev build lint test

run:
	python main.py

docker-build:
	docker build --target production -t ai-trading-system:latest .
	docker build --target test -t ai-trading-system:test .

docker-test:
	docker compose run --rm test

docker-run:
	docker compose up trading-system --build

clean:
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
