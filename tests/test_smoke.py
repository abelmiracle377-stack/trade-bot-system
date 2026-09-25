"""
Smoke tests – always run first.
These prove the package is importable and the basic pipeline pieces load
without any network or external services.
"""


def test_imports():
    """Core modules can be imported."""
    from src.data.fetcher import DataFetcher
    from src.features.engineer import FeatureEngineer
    from src.models.predictor import SignalPredictor
    from src.strategies.signal import SignalGenerator
    from src.risk.manager import RiskManager
    from src.backtest.engine import Backtester
    from src.portfolio.manager import PortfolioManager
    from src.utils.config import load_config
    from src.utils.logger import setup_logger

    assert DataFetcher is not None
    assert FeatureEngineer is not None
    assert SignalPredictor is not None
    assert SignalGenerator is not None
    assert RiskManager is not None
    assert Backtester is not None
    assert PortfolioManager is not None
    assert load_config is not None
    assert setup_logger is not None


def test_config_loads():
    """Config file exists and can be loaded."""
    from src.utils.config import load_config

    cfg = load_config("config/config.yaml")
    assert "data" in cfg
    assert "model" in cfg
    assert "risk" in cfg
    assert "backtest" in cfg
    assert isinstance(cfg["data"]["symbols"], list)
    assert len(cfg["data"]["symbols"]) > 0


def test_feature_engineer_basic():
    """FeatureEngineer can be instantiated and has expected attributes."""
    from src.features.engineer import FeatureEngineer

    eng = FeatureEngineer()
    assert hasattr(eng, "transform")
    assert hasattr(eng, "get_feature_columns")
    assert eng.rsi_period == 14
