"""Tests for configuration validation."""

import pytest

from src.utils.config import load_config
from src.utils.validation import assert_valid_config, validate_config


def test_valid_config_loads_cleanly():
    cfg = load_config("config/config.yaml")
    assert validate_config(cfg) == []


@pytest.mark.parametrize(
    ("mutator", "expected"),
    [
        (lambda c: c["data"].update(symbols=[]), "symbols"),
        (lambda c: c["data"].update(symbols=[""]), "symbols"),
        (lambda c: c["data"].update(symbols=["AAPL", 123]), "symbols"),
        (lambda c: c["model"].update(type="neural_net_v99"), "model.type"),
        (lambda c: c["model"].update(target_horizon=0), "target_horizon"),
        (lambda c: c["model"].update(train_test_split=1.0), "train_test_split"),
        (lambda c: c["backtest"].update(initial_capital=-1000), "initial_capital"),
        (lambda c: c["backtest"].update(commission_pct=-0.1), "commission_pct"),
        (lambda c: c["risk"].update(max_position_pct=1.1), "max_position_pct"),
    ],
)
def test_invalid_config_values_are_rejected(mutator, expected):
    cfg = load_config("config/config.yaml")
    mutator(cfg)
    errors = validate_config(cfg)
    assert any(expected in error for error in errors)


def test_assert_valid_config_raises():
    cfg = load_config("config/config.yaml")
    cfg["backtest"]["initial_capital"] = -1000
    with pytest.raises(ValueError, match="Invalid configuration"):
        assert_valid_config(cfg)


def test_load_config_rejects_non_mapping(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Configuration root"):
        load_config(config)
