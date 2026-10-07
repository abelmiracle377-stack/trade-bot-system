import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="TradeAI Broker API")

PAPER_BASE = "https://paper-api.alpaca.markets"
LIVE_BASE = "https://api.alpaca.markets"


def _token_ok(authorization: str | None) -> bool:
    expected = os.getenv("TRADING_API_TOKEN", "").strip()
    if not expected:
        return False
    return authorization == f"Bearer {expected}"


def _credentials(mode: str) -> tuple[str, str, str]:
    live = mode == "live"
    if live:
        if os.getenv("ALLOW_LIVE_TRADING", "").strip().upper() != "YES":
            raise HTTPException(403, "live_trading_not_enabled")
        if os.getenv("LIVE_TRADING_APPROVED", "").strip().upper() != "YES":
            raise HTTPException(403, "live_trading_not_approved")
    key = os.getenv("ALPACA_LIVE_API_KEY" if live else "ALPACA_PAPER_API_KEY", "").strip()
    secret = os.getenv("ALPACA_LIVE_API_SECRET" if live else "ALPACA_PAPER_API_SECRET", "").strip()
    if not key or not secret:
        # Backward-compatible fallback for the existing paper adapter.
        if not live:
            key = os.getenv("ALPACA_API_KEY", "").strip()
            secret = os.getenv("ALPACA_API_SECRET", "").strip()
    if not key or not secret:
        raise HTTPException(503, f"alpaca_{mode}_credentials_not_configured")
    return key, secret, LIVE_BASE if live else PAPER_BASE


def _alpaca(method: str, path: str, mode: str, payload: dict[str, Any] | None = None) -> Any:
    key, secret, base = _credentials(mode)
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(
        f"{base}{path}",
        data=body,
        method=method,
        headers={
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        try:
            detail = json.loads(detail)
        except json.JSONDecodeError:
            detail = {"message": detail[:500]}
        raise HTTPException(exc.code, detail) from exc
    except URLError as exc:
        raise HTTPException(502, f"alpaca_unreachable: {exc.reason}") from exc


class BrokerOrder(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    side: str
    qty: float = Field(gt=0)
    type: str = "market"
    time_in_force: str = "day"


def _require_token(authorization: str | None) -> None:
    if not _token_ok(authorization):
        raise HTTPException(401, "valid_bearer_token_required")


@app.get("/api/broker")
def broker_status(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    paper_key = bool(os.getenv("ALPACA_PAPER_API_KEY", "").strip() or os.getenv("ALPACA_API_KEY", "").strip())
    paper_secret = bool(os.getenv("ALPACA_PAPER_API_SECRET", "").strip() or os.getenv("ALPACA_API_SECRET", "").strip())
    live_key = bool(os.getenv("ALPACA_LIVE_API_KEY", "").strip())
    live_secret = bool(os.getenv("ALPACA_LIVE_API_SECRET", "").strip())
    return {
        "provider": "alpaca",
        "paper_configured": paper_key and paper_secret,
        "live_configured": live_key and live_secret,
        "live_enabled": os.getenv("ALLOW_LIVE_TRADING", "").strip().upper() == "YES"
        and os.getenv("LIVE_TRADING_APPROVED", "").strip().upper() == "YES",
    }


@app.get("/api/broker/account")
def broker_account(mode: str = "paper", authorization: str | None = Header(default=None)):
    _require_token(authorization)
    if mode not in {"paper", "live"}:
        raise HTTPException(400, "mode_must_be_paper_or_live")
    return _alpaca("GET", "/v2/account", mode)


@app.get("/api/broker/positions")
def broker_positions(mode: str = "paper", authorization: str | None = Header(default=None)):
    _require_token(authorization)
    if mode not in {"paper", "live"}:
        raise HTTPException(400, "mode_must_be_paper_or_live")
    return _alpaca("GET", "/v2/positions", mode)


@app.post("/api/broker/orders")
def broker_order(
    order: BrokerOrder,
    mode: str = "paper",
    authorization: str | None = Header(default=None),
):
    _require_token(authorization)
    if mode not in {"paper", "live"}:
        raise HTTPException(400, "mode_must_be_paper_or_live")
    side = order.side.lower()
    if side not in {"buy", "sell"}:
        raise HTTPException(400, "side_must_be_buy_or_sell")
    if order.type.lower() != "market":
        raise HTTPException(400, "only_market_orders_are_enabled")
    if mode == "live":
        # Live trading is deliberately behind two independent server-side gates.
        # The browser cannot enable either gate.
        _credentials("live")
    return _alpaca(
        "POST",
        "/v2/orders",
        mode,
        {
            "symbol": order.symbol.upper(),
            "qty": str(order.qty),
            "side": side,
            "type": "market",
            "time_in_force": order.time_in_force.lower(),
        },
    )
