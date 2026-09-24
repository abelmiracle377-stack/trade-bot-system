# AI Trading System – multi-stage Dockerfile
# Supports both running the pipeline and executing the test suite in isolation.

FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------- development / test image ----------
FROM base AS test
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
# Default command for the test stage: run the full suite
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]

# ---------- production image ----------
FROM base AS production
COPY . .
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader
CMD ["python", "main.py"]
