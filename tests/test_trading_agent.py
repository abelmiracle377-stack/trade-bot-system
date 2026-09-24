from datetime import datetime, timedelta, timezone

import pytest

from src.execution.agent import TradingAgent, TradingAgentConfig


class FakeBroker:
    def __init__(self, equity=100_000.0, qty=0.0):
        self.equity = equity
        self.qty = qty
        self.orders = []

    def account_equity(self):
        return self.equity

    def position_qty(self, symbol):
        return self.qty

    def submit_market_order(self, symbol, *, side, qty, client_order_id=None):
        self.orders.append((symbol, side, qty, client_order_id))
        self.qty += side * qty

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
    assert client_order_id == "ai-agent-aapl"


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
