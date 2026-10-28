-- Builds region_metrics: heat, canopy, risk score and double-burden flag per 2021 SA2.
-- Run by backend/build_metrics.py, which empties region_metrics first and fills in
-- :w_heat, :w_canopy and :w_irsd from settings.toml. Because of those placeholders,
-- this file does not run on its own in psql.
--
-- Steps:
--   covered     area-weighted heat and canopy per SA2 (see 2.1, 2.2)
--   with_seifa  adds IRSD; LEFT JOIN keeps the 5 SA2s without it (no residents)
--   scaled      0-1 scores (1 = worst) and heat quintile, over the 353 SA2s with IRSD only
--   final       weighted risk score and double-burden flag
--
-- Expected: 358 rows; 353 with a risk score; 18 with double_burden = true.

INSERT INTO region_metrics (
    sa2_code, heat_uhi, canopy_pct, covered_fraction,
    heat_scaled, canopy_scaled, irsd_scaled, risk_score,
    heat_quintile, double_burden
)
WITH covered AS (
    -- Mesh blocks are 2016 and SA2s 2021, so they are matched by shape and weighted by
    -- overlap area. Values are divided by the covered area, not the SA2 area, so land
    -- with no data is not counted as cool or treeless. SA2s under 1% covered (border
    -- slivers only: Romsey, Riddells Creek) are dropped. ::geography gives areas in m².
    SELECT s.sa2_code,
           sum(m.uhi * ST_Area(ST_Intersection(s.geom, m.geom)::geography))
             / sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography))                  AS heat_uhi,
           sum(m.tree_pct * ST_Area(ST_Intersection(s.geom, m.geom)::geography))
             / sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography))                  AS canopy_pct,
           sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography)) / 1000000 / s.area_sqkm AS covered_fraction
    FROM sa2 s
    JOIN mesh_block_heat_veg m
      ON ST_Intersects(s.geom, m.geom)
    GROUP BY s.sa2_code, s.area_sqkm
    HAVING sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography)) / 1000000 / s.area_sqkm >= 0.01
),
with_seifa AS (
    SELECT c.*, se.irsd_score, se.aus_decile
    FROM covered c
    LEFT JOIN seifa se
      ON se.sa2_code = c.sa2_code
),
scaled AS (
    -- Min-max scaling to 0-1, with canopy and IRSD flipped so 1 is always worst.
    -- FILTER (WHERE irsd_score IS NOT NULL) makes the min and max come from the 353
    -- SA2s with residents only, so airports and industrial land do not set the scale.
    SELECT w.*,
           CASE WHEN irsd_score IS NOT NULL THEN
               (heat_uhi - min(heat_uhi) FILTER (WHERE irsd_score IS NOT NULL) OVER ())
               / (max(heat_uhi) FILTER (WHERE irsd_score IS NOT NULL) OVER ()
                  - min(heat_uhi) FILTER (WHERE irsd_score IS NOT NULL) OVER ())
           END AS heat_scaled,
           CASE WHEN irsd_score IS NOT NULL THEN
               1 - (canopy_pct - min(canopy_pct) FILTER (WHERE irsd_score IS NOT NULL) OVER ())
                   / (max(canopy_pct) FILTER (WHERE irsd_score IS NOT NULL) OVER ()
                      - min(canopy_pct) FILTER (WHERE irsd_score IS NOT NULL) OVER ())
           END AS canopy_scaled,
           1 - (irsd_score - min(irsd_score) OVER ())
               / (max(irsd_score) OVER () - min(irsd_score) OVER ())                     AS irsd_scaled,
           -- PARTITION BY ranks the 353 with IRSD separately from the 5 without,
           -- and CASE then blanks the quintile for those 5.
           CASE WHEN irsd_score IS NOT NULL THEN
               ntile(5) OVER (PARTITION BY irsd_score IS NULL ORDER BY heat_uhi)
           END AS heat_quintile
    FROM with_seifa w
)
-- Double burden: hottest 20% within Melbourne AND bottom two national IRSD deciles.
-- NULL (not false) for SA2s without IRSD, because there is nothing to check.
SELECT sa2_code, heat_uhi, canopy_pct, covered_fraction,
       heat_scaled, canopy_scaled, irsd_scaled,
       :w_heat * heat_scaled + :w_canopy * canopy_scaled + :w_irsd * irsd_scaled          AS risk_score,
       heat_quintile,
       CASE WHEN irsd_score IS NOT NULL THEN heat_quintile = 5 AND aus_decile <= 2 END    AS double_burden
FROM scaled;
