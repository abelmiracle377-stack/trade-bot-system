"""Tests for the continuous paper-only bot runner."""
from __future__ import annotations

import json

import pytest

from scripts import run_paper_bot


def test_runner_rejects_too_short_interval() -> None:
    with pytest.raises(ValueError, match="at least 60"):
        run_paper_bot.run_bot(interval_seconds=30, once=True)


def test_once_runs_only_paper_cycle(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(run_paper_bot, "_run_cycle", lambda config_path, *, live: calls.append((config_path, live)))
    monkeypatch.setattr(run_paper_bot, "_write_run_status", lambda *args, **kwargs: None)

    failures = run_paper_bot.run_bot(config_path="test-config.yaml", interval_seconds=60, once=True)

    assert failures == 0
    assert calls == [("test-config.yaml", False)]


def test_cycle_failure_is_recorded_and_counted(monkeypatch: pytest.MonkeyPatch) -> None:
    statuses = []

    def fail_cycle(config_path: str, *, live: bool) -> None:
        raise RuntimeError("test broker unavailable")

    monkeypatch.setattr(run_paper_bot, "_run_cycle", fail_cycle)
    monkeypatch.setattr(run_paper_bot, "_write_run_status", lambda path, *, status, error=None: statuses.append((status, error)))

    failures = run_paper_bot.run_bot(interval_seconds=60, once=True)

    assert failures == 1
    assert statuses == [("paper_error", "test broker unavailable")]
