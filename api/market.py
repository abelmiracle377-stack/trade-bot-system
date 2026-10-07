from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="TradeAI Market API", version="0.1.0")

SUPPORTED = {
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "stocks": ["AAPL", "MSFT", "NVDA", "SPY"],
    "fx": [],
}

@app.get("/api/markets")
def markets():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supported": SUPPORTED,
        "note": "Broker/exchange credentials and live execution are intentionally not exposed by this endpoint.",
    }
