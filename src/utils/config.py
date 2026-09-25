"""Configuration loader with fail-fast validation."""

from pathlib import Path
from typing import Any, Dict

import yaml

from src.utils.validation import assert_valid_config


def load_config(path: str | Path = "config/config.yaml") -> Dict[str, Any]:
    """Load and validate a YAML configuration file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a mapping")

    assert_valid_config(config)
    return config


def get_nested(config: Dict[str, Any], *keys, default=None):
    """Safely get nested config value."""
    current = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
