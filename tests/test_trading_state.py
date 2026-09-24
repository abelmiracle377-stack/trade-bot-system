from datetime import date

from src.execution.state import RiskStateStore


def test_risk_state_persists_intraday_peak(tmp_path):
    path = tmp_path / "risk.json"
    store = RiskStateStore(str(path))

    state = store.load_or_initialize(date(2026, 9, 24), 100_000.0)
    state.peak_equity = 105_000.0
    store.save(state)

    restored = store.load_or_initialize(date(2026, 9, 24), 101_000.0)

    assert restored.peak_equity == 105_000.0


def test_risk_state_resets_on_new_trading_day(tmp_path):
    path = tmp_path / "risk.json"
    store = RiskStateStore(str(path))

    state = store.load_or_initialize(date(2026, 9, 24), 100_000.0)
    state.peak_equity = 105_000.0
    store.save(state)

    restored = store.load_or_initialize(date(2026, 9, 25), 101_000.0)

    assert restored.trading_day == "2026-09-25"
    assert restored.peak_equity == 101_000.0
