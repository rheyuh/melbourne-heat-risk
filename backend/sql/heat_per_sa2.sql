-- Area-weighted mean urban heat (UHI) for each 2021 SA2 in Greater Melbourne.
--
-- Why spatial: the heat data is on 2016 mesh blocks with 2016 codes, which do not
-- match 2021 SA2 codes, so mesh blocks are matched to SA2s by overlapping shape.
--
-- Why area-weighted: each mesh block counts in proportion to how many m² of the SA2
-- it covers, so mesh blocks crossing an SA2 border, and slivers along it, get the
-- right (often tiny) weight.
--
-- Coverage cut-off: an SA2 needs at least 1% of its area covered by heat data.
-- This removes SA2s whose only "data" is a border sliver (Romsey: 19 m²,
-- Riddells Creek: 4.7 m²). Partly covered SA2s are kept; covered_fraction shows how
-- much of each SA2 the heat value is based on (e.g. Kinglake 0.03, Bacchus Marsh 0.06).
--
-- ::geography makes ST_Area return m² (the stored geometry is lat/long, EPSG:7844).
--
-- Expected: 358 rows. Hand check: Footscray (213031348) = 9.3914.

SELECT s.sa2_code,
       sum(m.uhi * ST_Area(ST_Intersection(s.geom, m.geom)::geography))
         / sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography))                  AS heat_uhi,
       sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography)) / 1000000 / s.area_sqkm AS covered_fraction
FROM sa2 s
JOIN mesh_block_heat_veg m
  ON ST_Intersects(s.geom, m.geom)
GROUP BY s.sa2_code, s.area_sqkm
HAVING sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography)) / 1000000 / s.area_sqkm >= 0.01;
