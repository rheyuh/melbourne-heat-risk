"""Data layer: SQL for the API. Takes a connection, returns plain Python data."""

from sqlalchemy import text

# Simplify to ~10 m (0.0001° at Melbourne latitude): shrinks /regions from 6.4 MB to ~775 kB.
# Cost: boundaries can be up to ~10 m off and neighbours may show thin gaps; lookups use the full geometry.
SIMPLIFY_TOLERANCE = 0.0001
COORD_DECIMALS = 5

REGIONS_SQL = text("""
    SELECT  s.sa2_code,
            s.sa2_name,
            m.risk_score,
            m.double_burden,
            ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(s.geom, :tolerance), 4326), :decimals) AS geometry
    FROM sa2 s
    LEFT JOIN region_metrics m USING (sa2_code)
    ORDER BY s.sa2_code
""")

REGION_SQL = text("""
    SELECT  s.sa2_code, s.sa2_name, s.area_sqkm,
            m.heat_uhi, m.canopy_pct, m.covered_fraction,
            m.heat_scaled, m.canopy_scaled, m.irsd_scaled,
            m.risk_score, m.heat_quintile, m.double_burden,
            se.irsd_score, se.vic_decile, se.population
    FROM sa2 s
    LEFT JOIN region_metrics m USING (sa2_code)
    LEFT JOIN seifa se USING (sa2_code)
    WHERE s.sa2_code = :sa2_code
""")

DATASETS_SQL = text("""
    SELECT id, title, publisher, licence, source_url
    FROM datasets
    ORDER BY id
""")

def ping(conn):
    conn.execute(text("SELECT 1"))

def fetch_regions(conn):
    params = {"tolerance": SIMPLIFY_TOLERANCE, "decimals": COORD_DECIMALS}
    result = conn.execute(REGIONS_SQL, params)

    regions = []
    for row in result.mappings():
        regions.append(dict(row))
    return regions

def fetch_region(conn, sa2_code):
    row = conn.execute(REGION_SQL, {"sa2_code": sa2_code}).mappings().first()
    if row is None:
        return None
    return dict(row)

def fetch_datasets(conn):
    result = conn.execute(DATASETS_SQL)
    datasets = []
    for row in result.mappings():
        datasets.append(dict(row))
    return datasets