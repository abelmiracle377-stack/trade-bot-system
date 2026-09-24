import pytest

import src.execution.alpaca as alpaca_module
from src.execution.alpaca import AlpacaBroker


class FakeTradingClient:
    def __init__(self, key, secret, paper):
        self.paper = paper


def test_live_trading_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")
    monkeypatch.delenv("ALLOW_LIVE_TRADING", raising=False)
    monkeypatch.setattr(alpaca_module, "TradingClient", FakeTradingClient)

    with pytest.raises(RuntimeError, match="Live trading is disabled"):
        AlpacaBroker(paper=False)


def test_paper_trading_is_allowed_without_live_opt_in(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_API_SECRET", "secret")
    monkeypatch.delenv("ALLOW_LIVE_TRADING", raising=False)
    monkeypatch.setattr(alpaca_module, "TradingClient", FakeTradingClient)

    broker = AlpacaBroker(paper=True)

    assert broker.paper is True
