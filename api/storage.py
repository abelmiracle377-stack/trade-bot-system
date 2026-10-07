import os

def storage_status():
    url=os.getenv("DATABASE_URL","").strip()
    return {"configured":bool(url),"provider":"postgresql" if url else None}
