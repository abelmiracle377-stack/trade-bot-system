from fastapi import FastAPI
from datetime import datetime, timezone
app=FastAPI(title="TradeAI Account API")
@app.get("/api/account")
def demo_account():
    return {"mode":"paper","currency":"USD","equity":100000.0,"cash":100000.0,"buying_power":100000.0,"open_positions":[],"automation_enabled":False,"updated_at":datetime.now(timezone.utc).isoformat()}
