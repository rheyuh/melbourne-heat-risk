-- Runs once, only when the database volume is empty (first start).
-- Editing this file later does nothing until: docker compose down -v && docker compose up -d
-- Mounted by docker-compose.yml; runs after 10_postgis.sh (alphabetical order).
-- All geometry is GDA2020 lat/long (EPSG:7844), the same as the source files.

CREATE TABLE sa2 (
    sa2_code            text                            PRIMARY KEY,
    sa2_name            text                            NOT NULL,
    area_sqkm           double precision,
    geom                geometry(MultiPolygon, 7844)    NOT NULL
);

CREATE INDEX sa2_geom_idx ON sa2 USING GIST (geom);

CREATE TABLE seifa (
    sa2_code            text                            PRIMARY KEY REFERENCES sa2 (sa2_code),
    irsd_score          double precision                NOT NULL,
    aus_rank            integer,
    aus_decile          integer                         NOT NULL,
    vic_rank            integer,
    vic_decile          integer NOT NULL,
    population          integer
);

CREATE TABLE mesh_block_heat_veg (
    mb_code             text                            PRIMARY KEY,
    lga                 text,
    uhi                 double precision                NOT NULL,
    tree_pct            double precision                NOT NULL,
    tree_3_10_pct       double precision,
    tree_10_15_pct      double precision,
    tree_15_plus_pct    double precision,
    geom                geometry(MultiPolygon, 7844)    NOT NULL
);

CREATE INDEX mesh_block_heat_veg_geom_idx ON mesh_block_heat_veg USING GIST (geom);

CREATE TABLE datasets (
    id                  text                            PRIMARY KEY,
    title               text                            NOT NULL,
    publisher           text                            NOT NULL,
    licence             text                            NOT NULL,
    source_url          text,
    released            date,
    loaded_at           timestamptz                     NOT NULL DEFAULT now()
);