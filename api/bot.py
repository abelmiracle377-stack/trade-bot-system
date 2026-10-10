"""TradeAI server-side paper bot API.

POST /api/bot with {"action":"cycle"} analyzes Alpaca paper-market bars and
may place a risk-sized paper order. GET /api/bot returns account/position state.
Only Alpaca paper endpoints are used; live trading is not supported here.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="TradeAI Paper Bot API", version="1.0.0")
PAPER_BASE = "https://paper-api.alpaca.markets"
DATA_BASE = "https://data.alpaca.markets"
WATCHLIST = ["SPY", "AAPL", "MSFT", "NVDA"]
MAX_POSITION_FRACTION = 0.05
MAX_NEW_ORDERS_PER_CYCLE = 1


class CycleRequest(BaseModel):
    action: str = "cycle"


def _credentials() -> tuple[str, str]:
    key = os.getenv("ALPACA_API_KEY", "").strip()
    secret = os.getenv("ALPACA_API_SECRET", "").strip()
    if not key or not secret:
        raise HTTPException(503, {"code": "paper_broker_not_configured", "message": "Add ALPACA_API_KEY and ALPACA_API_SECRET as Vercel server-side environment variables using Alpaca paper-trading credentials."})
    return key, secret


def _request(url: str, *, key: str, secret: str, method: str = "GET", payload: dict | None = None, data_api: bool = False):
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        req = Request(url, data=body, headers=headers, method=method)
        with urlopen(req, timeout=12) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise HTTPException(exc.code if 400 <= exc.code < 500 else 502, {"code": "broker_request_failed", "message": detail}) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(502, {"code": "broker_unavailable", "message": "Could not reach the paper broker or market-data API."}) from exc


def _bars(symbol: str, key: str, secret: str) -> list[dict]:
    query = urlencode({"timeframe": "1Hour", "limit": 100, "feed": "iex"})
    data = _request(f"{DATA_BASE}/v2/stocks/{symbol}/bars?{query}", key=key, secret=secret, data_api=True)
    bars = data.get("bars") or []
    if len(bars) < 55:
        raise HTTPException(502, {"code": "insufficient_market_data", "message": f"Not enough hourly bars for {symbol}."})
    return bars


def _analyze(symbol: str, bars: list[dict]) -> dict:
    closes = [float(bar["c"]) for bar in bars]
    fast_now = sum(closes[-20:]) / 20
    slow_now = sum(closes[-50:]) / 50
    fast_prev = sum(closes[-21:-1]) / 20
    slow_prev = sum(closes[-51:-1]) / 50
    changes = [closes[i] - closes[i - 1] for i in range(len(closes) - 14, len(closes))]
    gains = sum(max(change, 0) for change in changes) / 14
    losses = sum(max(-change, 0) for change in changes) / 14
    rsi = 100.0 if losses == 0 else 100 - 100 / (1 + gains / losses)
    # Trade only on a confirmed moving-average cross; RSI avoids chasing extremes.
    signal = "BUY" if fast_prev <= slow_prev and fast_now > slow_now and 45 <= rsi <= 68 else "SELL" if fast_prev >= slow_prev and fast_now < slow_now and 32 <= rsi <= 55 else "HOLD"
    return {"symbol": symbol, "price": closes[-1], "sma20": round(fast_now, 4), "sma50": round(slow_now, 4), "rsi14": round(rsi, 2), "signal": signal, "bar_time": bars[-1].get("t")}


def _snapshot(key: str, secret: str) -> dict:
    account = _request(f"{PAPER_BASE}/v2/account", key=key, secret=secret)
    positions = _request(f"{PAPER_BASE}/v2/positions", key=key, secret=secret)
    orders = _request(f"{PAPER_BASE}/v2/orders?status=all&limit=20&direction=desc", key=key, secret=secret)
    return {"mode": "PAPER", "account": {"status": account.get("status"), "equity": account.get("equity"), "cash": account.get("cash"), "buying_power": account.get("buying_power"), "currency": account.get("currency", "USD")}, "positions": positions, "orders": orders, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/bot")
def status():
    key, secret = _credentials()
    return _snapshot(key, secret)


@app.post("/api/bot")
def cycle(body: CycleRequest):
    if body.action != "cycle":
        raise HTTPException(400, "action_must_be_cycle")
    key, secret = _credentials()
    snap = _snapshot(key, secret)
    account = snap["account"]
    try:
        equity = float(account.get("equity") or 0)
        cash = float(account.get("cash") or 0)
    except (TypeError, ValueError):
        raise HTTPException(502, "invalid_account_values")
    if equity <= 0 or cash <= 0:
        raise HTTPException(409, "paper_account_has_no_available_equity_or_cash")
    existing = {str(p.get("symbol", "")).upper(): p for p in snap["positions"]}
    analysis = []
    candidates = []
    for symbol in WATCHLIST:
        try:
            item = _analyze(symbol, _bars(symbol, key, secret))
            analysis.append(item)
            if item["signal"] == "BUY" and symbol not in existing:
                candidates.append(item)
        except HTTPException as exc:
            analysis.append({"symbol": symbol, "signal": "UNAVAILABLE", "reason": str(exc.detail)[:180]})
    placed = None
    if candidates and MAX_NEW_ORDERS_PER_CYCLE:
        chosen = max(candidates, key=lambda item: item["rsi14"])
        notional = min(equity * MAX_POSITION_FRACTION, cash * 0.95)
        qty = round(notional / chosen["price"], 6)
        if qty > 0 and qty * chosen["price"] >= 1:
            # Bracket protection is attached atomically to the entry order.
            payload = {"symbol": chosen["symbol"], "qty": str(qty), "side": "buy", "type": "market", "time_in_force": "day", "order_class": "bracket", "take_profit": {"limit_price": f"{chosen['price'] * 1.04:.2f}"}, "stop_loss": {"stop_price": f"{chosen['price'] * 0.98:.2f}"}, "client_order_id": "tradeai-paper-" + chosen["symbol"].lower() + "-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}
            placed = _request(f"{PAPER_BASE}/v2/orders", key=key, secret=secret, method="POST", payload=payload)
    refreshed = _snapshot(key, secret)
    return {"mode": "PAPER", "analysis": analysis, "order_submitted": placed, "account": refreshed["account"], "positions": refreshed["positions"], "orders": refreshed["orders"], "timestamp": datetime.now(timezone.utc).isoformat(), "policy": {"watchlist": WATCHLIST, "max_position_pct": MAX_POSITION_FRACTION * 100, "max_new_orders_per_cycle": MAX_NEW_ORDERS_PER_CYCLE, "stop_loss_pct": 2, "take_profit_pct": 4, "strategy": "Hourly SMA20/SMA50 crossover with RSI filter", "live_trading": False}}
