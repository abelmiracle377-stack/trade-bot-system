"""Tests for config validation."""

import pytest
from src.utils.validation import validate_config, assert_valid_config
from src.utils.config import load_config


def test_valid_config_loads_cleanly():
    cfg = load_config("config/config.yaml")
    errors = validate_config(cfg)
    assert errors == []


def test_missing_symbols_rejected():
    cfg = load_config("config/config.yaml")
    cfg["data"]["symbols"] = []
    errors = validate_config(cfg)
    assert any("symbols" in e for e in errors)


def test_bad_model_type_rejected():
    cfg = load_config("config/config.yaml")
    cfg["model"]["type"] = "neural_net_v99"
    errors = validate_config(cfg)
    assert any("model.type" in e or "Unsupported" in e for e in errors)


def test_assert_valid_config_raises():
    cfg = load_config("config/config.yaml")
    cfg["backtest"]["initial_capital"] = -1000
    with pytest.raises(ValueError, match="Invalid configuration"):
        assert_valid_config(cfg)
