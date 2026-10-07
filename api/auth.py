import os
from fastapi import FastAPI
app=FastAPI(title="TradeAI Auth API")
@app.get("/api/auth")
def auth_status():
    provider=os.getenv("AUTH_PROVIDER","").strip()
    return {"configured":bool(provider),"provider":provider or None,"message":"Managed authentication must be configured before real credentials are accepted."}
