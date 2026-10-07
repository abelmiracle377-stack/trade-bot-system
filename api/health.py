from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="TradeAI API", version="0.1.0")

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "tradeai-api",
        "paper_trading_default": True,
        "live_trading": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
