"""Web layer: routes, status codes and response formats."""

import json

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import Connection
from sqlalchemy.exc import OperationalError

import queries
from db import get_engine

app = FastAPI(title="Melbourne Heat Risk Explorer API")
engine = get_engine()

def get_conn():
    with engine.connect() as conn:
        yield conn

@app.exception_handler(OperationalError)
async def database_unavailable(request, exc):
    return JSONResponse(status_code=503, content={"detail": "database unreachable"})

@app.get("/health")
def health(conn: Connection = Depends(get_conn)):
    queries.ping(conn)
    return {"status": "ok", "database": "reachable"}

@app.get("/regions")
def list_regions(conn: Connection = Depends(get_conn)):
    features = []
    for region in queries.fetch_regions(conn):
        features.append(to_feature(region))
    return {"type": "FeatureCollection", "features": features}

def to_feature(region):
    return {
        "type": "Feature",
        "id": region["sa2_code"],
        "geometry": json.loads(region["geometry"]),
        "properties": {
            "sa2_code": region["sa2_code"],
            "sa2_name": region["sa2_name"],
            "risk_score": region["risk_score"],
            "double_burden": region["double_burden"],
        },
    }