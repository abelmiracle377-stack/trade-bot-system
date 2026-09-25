"""Configuration and input validation."""

from typing import Any, Dict, List

from loguru import logger


REQUIRED_TOP_LEVEL = ["data", "features", "model", "strategy", "risk", "backtest"]
SUPPORTED_MODELS = ("xgboost", "random_forest", "logistic")


def validate_config(cfg: Dict[str, Any]) -> List[str]:
    """Validate loaded YAML config and return actionable error messages."""
    errors: List[str] = []

    if not isinstance(cfg, dict):
        return ["Configuration root must be a mapping"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in cfg or not isinstance(cfg[key], dict):
            errors.append(f"Missing required mapping: '{key}'")

    data = cfg.get("data", {})
    symbols = data.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        errors.append("'data.symbols' must be a non-empty list")
    elif any(not isinstance(s, str) or not s.strip() for s in symbols):
        errors.append("'data.symbols' entries must be non-empty strings")

    model = cfg.get("model", {})
    model_type = model.get("type", "")
    if model_type not in SUPPORTED_MODELS:
        errors.append(f"Unsupported model.type: {model_type}")

    horizon = model.get("target_horizon", 5)
    if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= 60:
        errors.append("'model.target_horizon' must be an integer between 1 and 60")

    train_split = model.get("train_test_split", 0.8)
    if isinstance(train_split, bool) or not isinstance(train_split, (int, float)) or not 0 < train_split < 1:
        errors.append("'model.train_test_split' must be a number in (0, 1)")

    risk = cfg.get("risk", {})
    for pct_key in ("max_position_pct", "stop_loss_pct", "take_profit_pct", "max_drawdown_pct"):
        val = risk.get(pct_key)
        if val is not None and (
            isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0 or val > 1
        ):
            errors.append(f"'risk.{pct_key}' must be a number in (0, 1]")

    bt = cfg.get("backtest", {})
    capital = bt.get("initial_capital", 0)
    if isinstance(capital, bool) or not isinstance(capital, (int, float)) or capital <= 0:
        errors.append("'backtest.initial_capital' must be a positive number")

    for pct_key in ("commission_pct", "slippage_pct"):
        val = bt.get(pct_key)
        if val is not None and (
            isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0 or val > 1
        ):
            errors.append(f"'backtest.{pct_key}' must be a number in [0, 1]")

    if errors:
        for error in errors:
            logger.error(f"Config validation: {error}")
    return errors


def assert_valid_config(cfg: Dict[str, Any]) -> None:
    """Raise ValueError if config is invalid."""
    errors = validate_config(cfg)
    if errors:
        raise ValueError("Invalid configuration:\n  - " + "\n  - ".join(errors))
