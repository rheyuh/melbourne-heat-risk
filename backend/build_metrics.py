"""Rebuild region_metrics from the loaded tables. Run after ingest.py."""
from sqlalchemy import text

from config import BACKEND_DIR, RISK_WEIGHTS
from ingest import get_engine

BUILD_SQL = BACKEND_DIR / "sql" / "build_region_metrics.sql"

def build_region_metrics(engine, weights=None):
    if weights is None:
        weights = RISK_WEIGHTS
    sql = text(BUILD_SQL.read_text())
    params = {
        "w_heat": weights["heat"],
        "w_canopy": weights["canopy"],
        "w_irsd": weights["irsd"],
    }

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE region_metrics"))
        result = conn.execute(sql, params)
    print(f"region_metrics: {result.rowcount} rows")

if __name__ == "__main__":
    build_region_metrics(get_engine())
