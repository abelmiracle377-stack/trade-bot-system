import os
from fastapi import FastAPI

app = FastAPI(title="TradeAI Storage API")


def storage_status():
    url = os.getenv("DATABASE_URL", "").strip()
    return {"configured": bool(url), "provider": "postgresql" if url else None}


@app.get("/api/storage")
def storage():
    return storage_status()
