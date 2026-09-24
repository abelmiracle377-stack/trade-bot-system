from datetime import datetime, timedelta, timezone

import pytest

from src.execution.agent import TradingAgent, TradingAgentConfig


class FakeBroker:
    def __init__(self, equity=100_000.0, qty=0.0, gross=0.0, open_order=False):
        self.equity = equity
        self.qty = qty
        self.gross = gross or abs(qty * 100.0)
        self.open_order = open_order
        self.orders = []

    def account_equity(self):
        return self.equity

    def position_qty(self, symbol):
        return self.qty

    def gross_exposure(self, _price=None):
        return self.gross

    def has_open_order(self, symbol):
        return self.open_order

    def submit_market_order(self, symbol, *, side, qty, client_order_id=None):
        self.orders.append((symbol, side, qty, client_order_id))
        self.qty += side * qty
        self.gross = abs(self.qty * 100.0)

        class Result:
            order_id = "paper-test-order"
            status = "accepted"

        return Result()


def recent_timestamp():
    return datetime.now(timezone.utc) - timedelta(minutes=1)


def test_agent_submits_risk_checked_buy_order():
    broker = FakeBroker()
    agent = TradingAgent(
        broker,
        TradingAgentConfig(max_order_notional_pct=0.10),
    )

    result = agent.execute_signal(
        symbol="AAPL",
        signal=1,
        price=100.0,
        data_timestamp=recent_timestamp(),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is not None
    assert len(broker.orders) == 1
    symbol, side, qty, client_order_id = broker.orders[0]
    assert symbol == "AAPL"
    assert side == 1
    assert qty == pytest.approx(100.0)
    assert client_order_id.startswith("ai-agent-aapl-")
    assert len(client_order_id) > len("ai-agent-aapl-")


def test_agent_blocks_stale_market_data():
    broker = FakeBroker()
    agent = TradingAgent(broker)

    result = agent.execute_signal(
        symbol="AAPL",
        signal=1,
        price=100.0,
        data_timestamp=datetime.now(timezone.utc) - timedelta(hours=4),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is None
    assert broker.orders == []


def test_agent_blocks_daily_loss_limit():
    broker = FakeBroker(equity=96_000.0)
    agent = TradingAgent(broker)

    result = agent.execute_signal(
        symbol="AAPL",
        signal=1,
        price=100.0,
        data_timestamp=recent_timestamp(),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is None
    assert broker.orders == []


def test_agent_closes_position_even_after_opening_kill_switch():
    broker = FakeBroker(equity=96_000.0, qty=10.0, gross=1_000.0)
    agent = TradingAgent(broker, TradingAgentConfig(min_order_notional=10_000.0))

    result = agent.execute_signal(
        symbol="AAPL",
        signal=0,
        price=100.0,
        data_timestamp=datetime.now(timezone.utc) - timedelta(hours=12),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is not None
    assert broker.orders[0][1] == -1
    assert broker.orders[0][2] == pytest.approx(10.0)


def test_agent_blocks_order_that_would_exceed_portfolio_leverage():
    broker = FakeBroker(equity=100_000.0, qty=0.0, gross=95_000.0)
    agent = TradingAgent(
        broker,
        TradingAgentConfig(max_order_notional_pct=0.10, max_leverage=1.0),
    )

    result = agent.execute_signal(
        symbol="AAPL",
        signal=1,
        price=100.0,
        data_timestamp=recent_timestamp(),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is None
    assert broker.orders == []


def test_agent_blocks_when_symbol_has_open_order():
    broker = FakeBroker(open_order=True)
    agent = TradingAgent(broker)

    result = agent.execute_signal(
        symbol="AAPL",
        signal=1,
        price=100.0,
        data_timestamp=recent_timestamp(),
        start_of_day_equity=100_000.0,
        peak_equity=100_000.0,
    )

    assert result is None
    assert broker.orders == []
