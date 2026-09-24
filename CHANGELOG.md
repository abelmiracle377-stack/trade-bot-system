# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-09-24

### Added
- Config validation (`src/utils/validation.py`) with tests
- SECURITY.md with threat model notes
- Dependabot configuration for weekly dependency updates
- Per-symbol exception handling with full traceback logging in the main pipeline

### Changed
- CI treats mypy / bandit / safety as blocking
- Coverage gate at 65%

## [0.2.0] - 2026-09-24

### Added
- Experiment tracking via `scripts/run_experiment.py`
- Baseline comparison tests (`tests/test_model_baseline.py`)
- Structured / JSON logging with `run_id` context
- `tests/test_logger.py` and `tests/test_smoke.py`
- CHANGELOG.md

### Improved
- Documentation for reproducible experiments
- Error context when processing individual symbols

## [0.1.0] - 2026-09-24

### Added
- Initial modular AI trading research system
- Data fetching, feature engineering, ML signal generation
- Risk management and multi-asset backtester
- Full pytest suite, Docker, CI, Makefile
