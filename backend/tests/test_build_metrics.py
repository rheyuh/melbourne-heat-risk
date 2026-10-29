"""Tests for the region_metrics build, on a tiny hand-made map with known answers."""
import pytest
from sqlalchemy import text

from build_metrics import build_region_metrics

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

EQUAL_WEIGHTS = {"heat": 1 / 3, "canopy": 1 / 3, "irsd": 1 / 3}

# Worked out by hand: (heat_scaled, canopy_scaled, irsd_scaled, risk_score).
# Scaling uses S1-S5 only: heat 2-14, canopy 5-50, IRSD 800-1100.
EXPECTED_SCORES = {
    "S1": (1 / 2, 4 / 9, 2 / 3, 29 / 54),
    "S2": (1 / 6, 0,     0,     1 / 18),
    "S3": (5 / 6, 1,     1,     17 / 18),
    "S4": (0,     2 / 9, 1 / 3, 5 / 27),
    "S5": (1,     7 / 9, 1 / 2, 41 / 54),
}


def close(expected):
    # Geography areas are not perfectly proportional to width (edges curve slightly
    # on the Earth), so compare to 3 decimal places.
    return pytest.approx(expected, abs=1e-3)


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


def build(engine, weights):
    build_region_metrics(engine, weights)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM region_metrics")).mappings()
        return {row["sa2_code"]: row for row in rows}


@pytest.fixture
def metrics(engine, pretend_map):
    return build(engine, EQUAL_WEIGHTS)


def test_one_row_per_covered_sa2(metrics):
    # S7 has SEIFA but no heat data. It touches m7 along an edge (zero overlap,
    # like Romsey's sliver), so the 1% coverage cut-off must drop it.
    assert sorted(metrics) == ["S1", "S2", "S3", "S4", "S5", "S6"]


def test_area_weighting(metrics):
    # S1: 2 units of m1 and 1 unit of m2 (which crosses into S2).
    assert metrics["S1"]["heat_uhi"] == close((10 * 2 + 4 * 1) / 3)
    assert metrics["S1"]["canopy_pct"] == close((20 * 2 + 50 * 1) / 3)
    assert metrics["S1"]["covered_fraction"] == close(1)
    # S2 gets its values only from its half of m2.
    assert metrics["S2"]["heat_uhi"] == close(4)
    assert metrics["S2"]["canopy_pct"] == close(50)


@pytest.mark.parametrize("code", EXPECTED_SCORES)
def test_scaled_scores_and_risk(metrics, code):
    heat, canopy, irsd, risk = EXPECTED_SCORES[code]
    row = metrics[code]
    assert row["heat_scaled"] == close(heat)
    assert row["canopy_scaled"] == close(canopy)
    assert row["irsd_scaled"] == close(irsd)
    assert row["risk_score"] == close(risk)


def test_heat_quintile_and_double_burden(metrics):
    quintiles = {code: row["heat_quintile"] for code, row in metrics.items() if code != "S6"}
    assert quintiles == {"S4": 1, "S2": 2, "S1": 3, "S3": 4, "S5": 5}
    # S5: hottest quintile and decile 2, so flagged.
    # S3: decile 1 but only quintile 4, so not flagged (like Broadmeadows).
    flags = {code: row["double_burden"] for code, row in metrics.items() if code != "S6"}
    assert flags == {"S1": False, "S2": False, "S3": False, "S4": False, "S5": True}


def test_sa2_without_irsd_keeps_heat_but_has_no_scores(metrics):
    row = metrics["S6"]
    assert row["heat_uhi"] == close(16)
    assert row["canopy_pct"] == close(0)
    for column in ["heat_scaled", "canopy_scaled", "irsd_scaled",
                   "risk_score", "heat_quintile", "double_burden"]:
        assert row[column] is None, column


def test_weights_are_used(engine, pretend_map):
    # With all the weight on heat, every risk score must equal its heat score.
    heat_only = build(engine, {"heat": 1, "canopy": 0, "irsd": 0})
    for code in EXPECTED_SCORES:
        assert heat_only[code]["risk_score"] == close(heat_only[code]["heat_scaled"])
