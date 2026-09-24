"""Lightweight config and input validation."""

from typing import Any, Dict, List
from loguru import logger


REQUIRED_TOP_LEVEL = ["data", "features", "model", "strategy", "risk", "backtest"]


def validate_config(cfg: Dict[str, Any]) -> List[str]:
    """
    Validate the loaded YAML config.
    Returns a list of error messages (empty = valid).
    """
    errors: List[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in cfg:
            errors.append(f"Missing required top-level key: '{key}'")

    data = cfg.get("data", {})
    symbols = data.get("symbols")
    if not symbols or not isinstance(symbols, list) or len(symbols) == 0:
        errors.append("'data.symbols' must be a non-empty list")

    model = cfg.get("model", {})
    model_type = model.get("type", "")
    if model_type not in ("xgboost", "random_forest", "logistic"):
        errors.append(f"Unsupported model.type: {model_type}")

    horizon = model.get("target_horizon", 5)
    if not isinstance(horizon, int) or horizon < 1 or horizon > 60:
        errors.append("'model.target_horizon' must be an integer between 1 and 60")

    risk = cfg.get("risk", {})
    for pct_key in ("max_position_pct", "stop_loss_pct", "take_profit_pct", "max_drawdown_pct"):
        val = risk.get(pct_key)
        if val is not None and (not isinstance(val, (int, float)) or val <= 0 or val > 1):
            errors.append(f"'risk.{pct_key}' must be a float in (0, 1]")

    bt = cfg.get("backtest", {})
    capital = bt.get("initial_capital", 0)
    if not isinstance(capital, (int, float)) or capital <= 0:
        errors.append("'backtest.initial_capital' must be a positive number")

    if errors:
        for e in errors:
            logger.error(f"Config validation: {e}")
    return errors


def assert_valid_config(cfg: Dict[str, Any]) -> None:
    """Raise ValueError if config is invalid."""
    errors = validate_config(cfg)
    if errors:
        raise ValueError("Invalid configuration:\n  - " + "\n  - ".join(errors))
