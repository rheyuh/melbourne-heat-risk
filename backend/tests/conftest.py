"""Shared test setup: a throwaway PostGIS database built from the real schema."""
import os

import pytest
from sqlalchemy import text

from config import PROJECT_ROOT
from db import get_engine

SCHEMA_SQL = PROJECT_ROOT / "db" / "init" / "20_schema.sql"
TEST_DB = os.environ["POSTGRES_DB"] + "_test"


# The pretend map: seven square SA2s in a row. 1 unit = 0.01° of longitude, and all
# shapes share one band of latitude, so a shape's area is proportional to its width.
#
# unit:  0     1     2     3     4     5     6     7     8     9
# SA2s:  ├────── S1 ───────┼─ S2 ─┼─ S3 ─┼─ S4 ─┼─ S5 ─┼─ S6 ─┼─ S7 ─┤
# mesh:  ├──── m1 ────┼──── m2 ────┼─ m4 ─┼─ m5 ─┼─ m6 ─┼─ m7 ─┤  (none)

WEST = 145.0                 # longitude of unit 0
UNIT = 0.01                  # degrees of longitude per unit
SOUTH, NORTH = -37.81, -37.80

SA2S = {                     # code: (from unit, to unit)
    "S1": (0, 3), "S2": (3, 4), "S3": (4, 5), "S4": (5, 6),
    "S5": (6, 7), "S6": (7, 8), "S7": (8, 9),
}
MESH_BLOCKS = {              # code: (from unit, to unit, uhi, tree_pct)
    "m1": (0, 2, 10, 20),    # all in S1
    "m2": (2, 4, 4, 50),     # crosses the S1/S2 border: 1 unit in each
    "m4": (4, 5, 12, 5),
    "m5": (5, 6, 2, 40),
    "m6": (6, 7, 14, 15),
    "m7": (7, 8, 16, 0),     # hottest and least treed of all, but S6 has no residents
}
SEIFA = {                    # code: (irsd_score, aus_decile). S6 has no row, like an airport.
    "S1": (900, 3), "S2": (1100, 9), "S3": (800, 1), "S4": (1000, 7),
    "S5": (950, 2), "S7": (1050, 8),
}


@pytest.fixture(scope="session")
def engine():
    # CREATE/DROP DATABASE cannot run inside a transaction, so use autocommit.
    admin = get_engine().execution_options(isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))

    test_engine = get_engine(TEST_DB)
    with test_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION postgis"))
        conn.exec_driver_sql(SCHEMA_SQL.read_text())

    yield test_engine

    test_engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE {TEST_DB}"))


def corners(start, end):
    return {"x0": WEST + start * UNIT, "y0": SOUTH, "x1": WEST + end * UNIT, "y1": NORTH}


@pytest.fixture(scope="module")
def pretend_map(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE sa2, seifa, mesh_block_heat_veg, datasets, region_metrics"))
        for code, (start, end) in SA2S.items():
            conn.execute(text("""
                INSERT INTO sa2 (sa2_code, sa2_name, geom)
                VALUES (:code, :code, ST_Multi(ST_MakeEnvelope(:x0, :y0, :x1, :y1, 7844)))
            """), {"code": code, **corners(start, end)})
        conn.execute(text("UPDATE sa2 SET area_sqkm = ST_Area(geom::geography) / 1000000"))
        for code, (start, end, uhi, tree_pct) in MESH_BLOCKS.items():
            conn.execute(text("""
                INSERT INTO mesh_block_heat_veg (mb_code, uhi, tree_pct, geom)
                VALUES (:code, :uhi, :tree_pct, ST_Multi(ST_MakeEnvelope(:x0, :y0, :x1, :y1, 7844)))
            """), {"code": code, "uhi": uhi, "tree_pct": tree_pct, **corners(start, end)})
        for code, (irsd_score, decile) in SEIFA.items():
            conn.execute(text("""
                INSERT INTO seifa (sa2_code, irsd_score, aus_decile, vic_decile)
                VALUES (:code, :irsd_score, :decile, :decile)
            """), {"code": code, "irsd_score": irsd_score, "decile": decile})