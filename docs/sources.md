# Data sources

The raw files live in `data/raw/`, which is not committed. This file records where each one came
from so the data can be downloaded again and cited.

The SEIFA and heat facts below were checked with `backend/inspect_sources.py` (read-only; see the
docstring for how to run each check). The SA2 facts were checked with `sqlite3` queries on the
GeoPackage.

Storage CRS for the database: GDA2020 (EPSG:7844).

## ASGS 2021 Main Structure (SA2 layer used)

- Publisher: Australian Bureau of Statistics (ABS)
- Dataset: Australian Statistical Geography Standard (ASGS) Edition 3, July 2021 – June 2026,
  Main Structure and Greater Capital City Statistical Areas, GDA2020
- Layers in file: MB, SA1, SA2, SA3, SA4, GCCSA, STE, AUS (each `<LEVEL>_2021_AUST_GDA2020`)
- Layer used: `SA2_2021_AUST_GDA2020`
- Page URL: https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files
- File URL: https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files/ASGS_2021_MAIN_STRUCTURE_GPKG_GDA2020.zip
- Released: 2021-07-20
- Downloaded: 2026-10-17
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Format: GeoPackage (`.gpkg`), with ISO metadata `.xml` per layer
- CRS: GDA2020 geographic (EPSG:7844). Matches the storage CRS, so no reprojection needed.
- Local path: `data/raw/abs_asgs_2021/ASGS_2021_Main_Structure_GDA2020.gpkg`
- Coverage: All of Australia, 2,473 SA2s. Greater Melbourne: 361 SA2s
  (filter `GCCSA_CODE_2021 = '2GMEL'`).
- Key fields:
  - `SA2_CODE_2021` (TEXT(9)): join key for SEIFA
  - `SA2_NAME_2021`: display name
  - `GCCSA_CODE_2021`, `GCCSA_NAME_2021`: Greater Melbourne filter
  - `AREA_ALBERS_SQKM`: area from the ABS, useful to check `ST_Area` results
  - `CHANGE_FLAG_2021`, `CHANGE_LABEL_2021`: change since 2016 (2,065 no change, 304 new,
    104 name change)
  - `geom`: geometry; the file includes a spatial index
- Gotchas:
  - 19 rows have no geometry: "Migratory - Offshore - Shipping" and "No usual address", one
    of each per state and territory (Victoria: `297979799`, `299999499`). They have their own
    GCCSA codes (Victoria: `29799`, `29499`), so the `'2GMEL'` filter already excludes them.
  - Codes are text, not numbers. Keep them as text when joining.
  - Must match SEIFA 2021, so use ASGS Edition 3 (2021), not Edition 4 (2026).

## SEIFA 2021 by SA2 (IRSD used)

- Publisher: Australian Bureau of Statistics (ABS)
- Dataset: Socio-Economic Indexes for Areas (SEIFA), Australia, 2021: Statistical Area Level 2,
  Indexes
- Sheets in file: Contents, Table 1 (summary of all four indexes, rounded), Table 2 (IRSD),
  Table 3 (IRSAD), Table 4 (IER), Table 5 (IEO), Table 6 (Excluded Areas), Explanatory Notes
- Sheet used: `Table 2` (IRSD, unrounded scores)
- Page URL: https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/2021
- File URL: https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/2021/Statistical%20Area%20Level%202%2C%20Indexes%2C%20SEIFA%202021.xlsx
- Released: 2023-04-27
- Downloaded: 2026-10-17
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), the ABS standard licence
- Format: Excel workbook (`.xlsx`)
- CRS: None. It is a table with no geometry and joins to SA2 boundaries on the SA2 code.
- Local path: `data/raw/abs_seifa_2021/Statistical Area Level 2, Indexes, SEIFA 2021.xlsx`
- Coverage: All of Australia, 2,353 SA2s. Every code exists in ASGS 2021; 120 ASGS SA2s have no
  SEIFA row (no or very few residents; Table 6 lists the excluded areas). 5 Greater Melbourne
  SA2s have no IRSD score.
- Key fields (Table 2, by column position; the header is on spreadsheet row 6):
  - SA2 9-digit code: join key
  - SA2 name
  - Usual resident population
  - Score (national mean about 1000; lower means more disadvantaged)
  - Ranking within Australia: rank, decile, percentile
  - Ranking within state or territory: state, rank, decile, percentile
  - Minimum and maximum score of SA1s in the area; % of residents without an SA1 score
- Gotchas:
  - Five title rows above the header and a blank row plus a copyright line at the bottom. Skip
    them, or keep only rows whose first column is a 9-digit code.
  - The header spans two rows ("Ranking within Australia" sits above Rank/Decile/Percentile),
    and there are empty spacer columns between groups.
  - pandas reads the codes as integers. Convert them to text before joining to `SA2_CODE_2021`.
  - Scores are relative rankings, not measurements. Prefer deciles or ranks over arithmetic
    on raw scores.
  - Open question for Task 2: national or Victorian decile.

## Urban heat and vegetation 2018

- Publisher: Department of Transport and Planning (Victoria)
- Dataset: Metropolitan Melbourne Urban Heat Islands and Urban Vegetation 2018 (Plan Melbourne
  Action 91, "Cooling & Greening"); resource name `HEAT_URBAN_HEAT_2018`, metadata ID
  `ea69bd5e-3682-5326-b1ec-8e2964baa6a0`
- Layer used: `HEAT_URBAN_HEAT_2018` (the only layer in the file)
- Page URL: https://discover.data.vic.gov.au/dataset/metropolitan-melbourne-urban-heat-islands-and-urban-vegetation-2018
- File URL: None that lasts. Ordered through Vicmap DataShare
  (https://datashare.maps.vic.gov.au/search?md=ea69bd5e-3682-5326-b1ec-8e2964baa6a0), which
  emails a download link. Order settings: File Geodatabase, GDA2020 geographic, whole dataset,
  no buffer.
- Data dictionary: https://www.planning.vic.gov.au/__data/assets/pdf_file/0025/397402/Data-Dictionary-Vegetation-and-Heat-Mapping-Metro-Melbourne-2019-UPDATE.pdf
  (linked from the metadata, but returns HTTP 403 as of 2026-10-19; a newer copy at
  https://www.planning.vic.gov.au/__data/assets/pdf_file/0016/630124/data-dictionary-vegetation-and-heat-mapping-metro-melbourne.pdf
  is also blocked)
- Full metadata record: https://metashare.maps.vic.gov.au/geonetwork/srv/api/records/ea69bd5e-3682-5326-b1ec-8e2964baa6a0
- Released: 2019-07-06 (last updated 2023-09-04)
- Downloaded: 2026-10-17
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0); the DataShare order also
  includes `Data Access Licence Agreement DS.pdf`
- Format: Esri File Geodatabase (`.gdb` folder), plus a metadata PDF
- CRS: GDA2020 geographic (EPSG:7844), chosen at order time. DataShare did the conversion.
- Local path: `data/raw/vic_heat_vegetation_2018/ll_gda2020/filegdb/whole_of_dataset/victoria/PLANNING.gdb`
- Coverage: 55,603 MultiPolygons, one per 2016 ABS mesh block, all in 2016 Greater Melbourne
  (`GCC_CODE16 = 2GMEL`), across 35 LGAs. Against 2021 Greater Melbourne SA2s: 345 almost fully
  covered (95% or more), 13 partly covered (outer areas such as Wallan, Gisborne, Bacchus Marsh),
  3 not covered at all (Macedon, Romsey, Riddells Creek). No nulls in any field.
- Key fields:
  - `UHI18_M`: urban heat island value in °C, the mean difference in land surface temperature
    (Landsat-8) from a non-urban baseline. Mean 8.4, range −8.9 to 16.9.
  - `PERANYTREE`: % tree cover, equal to `PERTR03_10 + PERTR10_15 + PERTR15PL`
    (trees 3–10 m, 10–15 m, 15 m and taller)
  - `PERSHRUB`, `PERGRASS`, `PERSHRBTRE`, `PERANYVEG`: % shrub, grass, shrub or tree, and any
    vegetation
  - `MB_CODE16`, `SA1_MAIN16`, `SA2_MAIN16`, `SA3_CODE16`, `SA4_CODE16`, `GCC_CODE16`, `LGA`:
    2016 geography codes and council name
- Gotchas:
  - Polygons are 2016 mesh blocks carrying 2016 SA2 codes, which cannot be joined to 2021 codes
    (304 SA2s are new in 2021), so aggregation to SA2 has to be spatial. 55,591 of 55,603 mesh
    blocks sit inside a single 2021 SA2; 12 cross an edge, 7 of them by 10% or more (all in
    growth areas such as Melton South, Southbank and Pakenham). Area-weighting handles these
    exactly; assigning by centre point is simpler and wrong only for those few.
  - The heat value is land surface temperature, not air temperature, from a single 2018 capture.
  - 273 polygons have a negative heat value (cooler than the baseline), probably water or large
    parks. Check before using them in the index.
  - Vegetation year: most likely 2018. The sister dataset "Vegetation Cover for metropolitan
    Melbourne 2018" says it comes from "aerial photography and Near-Infrared (NIR) imagery as at
    2018", and this dataset is titled "Urban Vegetation 2018". Its own metadata mentions
    "modified Mesh Blocks as at 2014", which probably refers to the boundaries, not the imagery.
    The data dictionary that would confirm this is no longer online (HTTP 403 for both known
    links). Sister dataset record:
    https://metashare.maps.vic.gov.au/geonetwork/srv/api/records/88728f89-b1e1-5bba-9dce-04107c064fd2
  - Some outer Greater Melbourne SA2s have little or no data. The map needs a "no data" style.

## Raster or polygons?

The heat data is polygons, each one a 2016 mesh block. Because they use 2016 SA2 codes that
don't match the 2021 SA2s (304 are new), I have to combine them by location on the map instead
of by code; only a handful of mesh blocks (12 of 55,603) cross a 2021 SA2 edge.
