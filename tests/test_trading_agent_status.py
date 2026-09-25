import json

import pytest

import scripts.run_trading_agent as trading_agent


def test_run_writes_success_status(tmp_path, monkeypatch):
    status_path = tmp_path / "status.json"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(trading_agent, "_run_cycle", lambda *args, **kwargs: None)

    trading_agent.run()

    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["status"] == "success"
    assert "timestamp" in payload


def test_run_writes_failure_status_and_reraises(tmp_path, monkeypatch):
    status_path = tmp_path / "status.json"

    def fail(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(trading_agent, "_run_cycle", fail)

    with pytest.raises(RuntimeError, match="broker unavailable"):
        trading_agent.run()

    payload = json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["error"] == "broker unavailable"
