"""Shared test environment defaults; tests must still mock broker clients."""

import pytest


@pytest.fixture
def alpaca_test_credentials(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "test-secret")
    return "test-key", "test-secret"
