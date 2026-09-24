"""Configuration loader."""

from pathlib import Path
from typing import Any, Dict
import yaml


def load_config(path: str | Path = "config/config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config


def get_nested(config: Dict[str, Any], *keys, default=None):
    """Safely get nested config value."""
    current = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
