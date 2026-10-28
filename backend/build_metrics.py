"""Rebuild region_metrics from the loaded tables. Run after ingest.py."""
from sqlalchemy import text

from config import BACKEND_DIR, RISK_WEIGHTS
from ingest import get_engine

BUILD_SQL = BACKEND_DIR / "sql" / "build_region_metrics.sql"

def build_region_metrics(engine):
    sql = text(BUILD_SQL.read_text())
    weights = {
        "w_heat": RISK_WEIGHTS["heat"],
        "w_canopy": RISK_WEIGHTS["canopy"],
        "w_irsd": RISK_WEIGHTS["irsd"],
    }

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE region_metrics"))
        result = conn.execute(sql, weights)
    print(f"region_metrics: {result.rowcount} rows")

if __name__ == "__main__":
    build_region_metrics(get_engine())
