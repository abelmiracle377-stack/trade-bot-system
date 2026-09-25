import json
from types import SimpleNamespace

import pandas as pd

import scripts.run_experiment as experiment


def test_run_experiment_writes_a_reproducible_ledger_entry(tmp_path, monkeypatch):
    index = pd.date_range("2024-01-01", periods=8, freq="D")
    frame = pd.DataFrame(
        {
            "Close": [100, 101, 102, 101, 103, 104, 105, 106],
            "vol_20d": [0.2] * 8,
        },
        index=index,
    )

    class FakeFetcher:
        def __init__(self, cache_dir):
            self.cache_dir = cache_dir

        def fetch_multiple(self, symbols, start, end):
            return {symbol: frame.copy() for symbol in symbols[:1]}

    class FakeEngineer:
        def __init__(self, **kwargs):
            pass

        def transform(self, df):
            return df.copy()

        def get_feature_columns(self, df):
            return ["Close"]

    class FakePredictor:
        def __init__(self, model_type, target_horizon, model_params, random_state):
            self.model_type = model_type
            self.target_horizon = target_horizon
            self.random_state = random_state

        def fit(self, featured, feature_cols, test_size):
            return {"accuracy": 0.75, "roc_auc": 0.80}

        def metadata(self):
            return {
                "model_type": self.model_type,
                "target_horizon": self.target_horizon,
                "random_state": self.random_state,
                "feature_names": ["Close"],
            }

        def predict_proba(self, featured):
            return pd.Series([0.6] * len(featured), index=featured.index)

        def save(self, path):
            path.write_text("trusted-test-artifact", encoding="utf-8")

    class FakeBacktester:
        def __init__(self, **kwargs):
            pass

        def run(self, **kwargs):
            return SimpleNamespace(
                metrics={
                    "total_return": 0.12,
                    "sharpe_ratio": 1.4,
                    "n_trades": 3,
                }
            )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(experiment, "DataFetcher", FakeFetcher)
    monkeypatch.setattr(experiment, "FeatureEngineer", FakeEngineer)
    monkeypatch.setattr(experiment, "SignalPredictor", FakePredictor)
    monkeypatch.setattr(experiment, "Backtester", FakeBacktester)
    monkeypatch.setattr(experiment, "RiskManager", lambda **kwargs: object())
    monkeypatch.setattr(
        experiment,
        "SignalGenerator",
        lambda **kwargs: SimpleNamespace(generate=lambda probabilities: probabilities),
    )
    monkeypatch.setattr(experiment, "setup_logger", lambda **kwargs: None)

    record = experiment.run_experiment(
        "/unused/config.yaml",
        run_id="test_experiment_001",
    )

    assert record["run_id"] == "test_experiment_001"
    assert record["random_state"] == 42
    assert record["model_metadata"]["AAPL"]["feature_names"] == ["Close"]
    assert record["backtest_metrics"]["sharpe_ratio"] == 1.4

    ledger = tmp_path / "reports" / "experiment_log.jsonl"
    summary = tmp_path / "reports" / "test_experiment_001_summary.json"

    assert ledger.exists()
    assert summary.exists()
    assert json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])["run_id"] == "test_experiment_001"
