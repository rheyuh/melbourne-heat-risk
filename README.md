# Melbourne Heat Risk & Disadvantage Explorer

A map of urban heat, tree canopy and socio-economic disadvantage for every SA2 region in Greater
Melbourne. It asks one question: **which Melbourne suburbs carry the double burden of heat and
disadvantage?** Each region gets a transparent risk score built from public data, and regions that
are both among the hottest and among the most disadvantaged are flagged as "double burden". It is
aimed at researchers and planners who want to see where heat risk and disadvantage overlap, and
check how that result was reached. I built it to learn the kind of tooling behind
[AURIN's](https://aurin.org.au) urban climate risk work: loading open spatial data (from the
[ABS](https://www.abs.gov.au) and [data.vic.gov.au](https://www.data.vic.gov.au)) into PostGIS,
doing the spatial analysis in the database, and serving the results through an API to a web map.

## Status

Work in progress. Planned stack: Python (FastAPI, geopandas), PostgreSQL with PostGIS, React with
TypeScript and Leaflet, Docker Compose and GitHub Actions.
Progress is tracked on the [project board](https://github.com/users/rheyuh/projects/3).

## How to run

Coming soon.
