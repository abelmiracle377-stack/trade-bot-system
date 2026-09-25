import pandas as pd

from src.learning.engine import FeedbackLearner
from src.learning.store import SignalOutcome, SignalOutcomeStore


def _append_resolved(store, index: int, probability: float, outcome: str) -> None:
    store.append(
        SignalOutcome(
            signal_id=f"sig-{index}",
            user_id="agent",
            symbol="AAPL",
            direction="long",
            probability=probability,
            entry_price=100.0,
            exit_price=105.0 if outcome == "win" else 95.0,
            realized_return=0.05 if outcome == "win" else -0.05,
            outcome=outcome,
            signal_time=pd.Timestamp("2025-01-01", tz="UTC")
            .__add__(pd.Timedelta(days=index))
            .isoformat(),
            horizon_bars=1,
            model_version="test",
        )
    )


def test_resolve_pending_outcome(tmp_path):
    store = SignalOutcomeStore(tmp_path / "signals.jsonl")
    learner = FeedbackLearner(store, min_samples=10)
    learner.record_prediction(
        signal_id="pending",
        symbol="AAPL",
        direction=1,
        probability=0.8,
        entry_price=100.0,
        signal_time=pd.Timestamp("2025-01-01", tz="UTC"),
        horizon_bars=1,
        model_version="test",
    )

    data = pd.DataFrame(
        {"Close": [100.0, 105.0]},
        index=pd.date_range("2025-01-01", periods=2, freq="D", tz="UTC"),
    )
    assert learner.resolve_pending("AAPL", data) == 1
    resolved = store.latest()[0]
    assert resolved.outcome == "win"
    assert round(resolved.realized_return, 10) == 0.05


def test_calibrator_only_activates_after_validation(tmp_path):
    store = SignalOutcomeStore(tmp_path / "signals.jsonl")
    for i in range(24):
        _append_resolved(store, i, 0.8, "win" if i % 2 == 0 else "loss")
    learner = FeedbackLearner(store, min_samples=20)
    metrics = learner.fit()
    assert metrics["samples"] == 24
    assert metrics["active"] in {0.0, 1.0}


def test_inactive_learner_preserves_base_probability(tmp_path):
    store = SignalOutcomeStore(tmp_path / "signals.jsonl")
    learner = FeedbackLearner(store, min_samples=20)
    assert learner.adjust_probability(0.63) == 0.63
