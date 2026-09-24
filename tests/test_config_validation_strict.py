"""Regression tests for critical configuration bounds."""

from src.utils.validation import validate_config


def _valid_config():
    return {
        "data": {"symbols": ["AAPL"]},
        "features": {},
        "model": {
            "type": "logistic",
            "target_horizon": 5,
            "train_test_split": 0.8,
        },
        "strategy": {},
        "risk": {
            "max_position_pct": 0.15,
            "stop_loss_pct": 0.08,
            "take_profit_pct": 0.20,
            "max_drawdown_pct": 0.25,
        },
        "backtest": {
            "initial_capital": 100000,
            "commission_pct": 0.001,
            "slippage_pct": 0.0005,
        },
    }


def test_valid_config_has_no_errors():
    assert validate_config(_valid_config()) == []


def test_invalid_train_split_is_rejected():
    cfg = _valid_config()
    cfg["model"]["train_test_split"] = 1.0
    assert any("train_test_split" in error for error in validate_config(cfg))


def test_negative_transaction_cost_is_rejected():
    cfg = _valid_config()
    cfg["backtest"]["commission_pct"] = -0.01
    assert any("commission_pct" in error for error in validate_config(cfg))
