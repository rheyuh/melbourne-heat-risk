"""Web layer: routes, status codes and response formats."""
import json

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import Connection
from sqlalchemy.exc import OperationalError

import queries
from db import get_engine
from schemas import RegionDetail

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

@app.get("/regions/at", response_model=RegionDetail)
def get_region_at(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    conn: Connection = Depends(get_conn),
):
    sa2_code = queries.find_region_at(conn, lat, lon)
    if sa2_code is None:
        raise HTTPException(status_code=404, detail="No Greater Melbourne SA2 contains this point")
    region = queries.fetch_region(conn, sa2_code)
    region["sources"] = queries.fetch_datasets(conn)
    return region

@app.get("/regions/{sa2_code}", response_model=RegionDetail)
def get_region(sa2_code: str, conn: Connection = Depends(get_conn)):
    region = queries.fetch_region(conn, sa2_code)
    if region is None:
        raise HTTPException(status_code=404, detail=f"No SA2 with code {sa2_code}")
    region["sources"] = queries.fetch_datasets(conn)
    return region

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