-- Area-weighted urban heat (UHI) and tree canopy for each 2021 SA2 in Greater Melbourne.
--
-- Why spatial: the heat and vegetation data is on 2016 mesh blocks with 2016 codes, which
-- do not match 2021 SA2 codes, so mesh blocks are matched to SA2s by overlapping shape.
--
-- Why area-weighted: each mesh block counts in proportion to how many m² of the SA2
-- it covers, so mesh blocks crossing an SA2 border, and slivers along it, get the
-- right (often tiny) weight. For canopy, tree_pct × overlap is the m² of trees in each
-- piece (assuming trees are spread evenly within a mesh block).
--
-- Both values are divided by the area covered by data, not the whole SA2 area. The
-- data only covers urban land; dividing by the whole SA2 would count uncovered forest
-- and farmland as treeless (Kinglake: 30.5% canopy, but 0.9% over the whole SA2).
-- So heat and canopy both describe the same covered ground.
--
-- Coverage cut-off: an SA2 needs at least 1% of its area covered by data.
-- This removes SA2s whose only "data" is a border sliver (Romsey: 19 m²,
-- Riddells Creek: 4.7 m²). Partly covered SA2s are kept; covered_fraction shows how
-- much of each SA2 the values are based on (e.g. Kinglake 0.03, Bacchus Marsh 0.06).
--
-- ::geography makes ST_Area return m² (the stored geometry is lat/long, EPSG:7844).
-- Issue #47 suggested ST_Transform to EPSG:7855; geography is used here so heat and
-- canopy are measured the same way, and the two agree to within 0.1% for Melbourne.
--
-- Expected: 358 rows, canopy_pct between 0.84 and 47.5.
-- Hand checks: Footscray (213031348) heat_uhi = 9.3914, canopy_pct = 8.3385.

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
HAVING sum(ST_Area(ST_Intersection(s.geom, m.geom)::geography)) / 1000000 / s.area_sqkm >= 0.01;
