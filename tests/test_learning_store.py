from src.learning.store import SignalOutcome, SignalOutcomeStore


def test_signal_outcome_store_round_trip(tmp_path) -> None:
    store = SignalOutcomeStore(tmp_path / "signals.jsonl")
    record = SignalOutcome(
        signal_id="sig-1",
        user_id="user-1",
        symbol="AAPL",
        direction="long",
        probability=0.8,
        entry_price=100.0,
        exit_price=105.0,
        realized_return=0.05,
        outcome="win",
    )
    store.append(record)

    assert store.read() == [record]
