"""Read-only API over region_metrics."""

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import get_engine

app = FastAPI(title="Melbourne Heat Risk Explorer API")
engine = get_engine()

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        raise HTTPException(status_code=503, detail="database unreachable")
    return {"status": "ok", "database": "reachable"}