import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="TradeAI Candles API", version="1.0.0")

ALLOWED_SYMBOLS = {
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY",
}
ALLOWED_INTERVALS = {"1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h", "1day", "1week"}


@app.get("/api/candles")
def candles(
    symbol: str = Query(default="EUR/USD", max_length=12),
    interval: str = Query(default="15min", max_length=8),
    outputsize: int = Query(default=120, ge=30, le=500),
):
    symbol = symbol.upper().replace(" ", "")
    interval = interval.lower()
    if symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(400, "unsupported_forex_pair")
    if interval not in ALLOWED_INTERVALS:
        raise HTTPException(400, "unsupported_interval")
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(503, {
            "code": "forex_data_key_missing",
            "message": "Add TWELVE_DATA_API_KEY in Vercel Environment Variables to enable real forex candles.",
        })
    params = urlencode({
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "timezone": "UTC",
        "apikey": api_key,
    })
    request = Request(
        "https://api.twelvedata.com/time_series?" + params,
        headers={"Accept": "application/json", "User-Agent": "TradeAI/1.0"},
    )
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(502, "forex_data_provider_http_error") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(502, "forex_data_provider_unavailable") from exc
    if payload.get("status") == "error" or "values" not in payload:
        message = str(payload.get("message", "Forex data provider returned no candle data"))
        raise HTTPException(502, {"code": "forex_data_provider_error", "message": message[:240]})
    values = []
    for row in reversed(payload.get("values", [])):
        try:
            values.append({
                "time": row["datetime"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume") or 0),
            })
        except (KeyError, TypeError, ValueError):
            continue
    if len(values) < 20:
        raise HTTPException(502, "not_enough_candle_data")
    return {
        "symbol": symbol,
        "interval": interval,
        "source": "Twelve Data",
        "timestamp": payload.get("meta", {}).get("exchange_timezone", "UTC"),
        "candles": values,
    }
