from datetime import date
from sqlalchemy import text
import geopandas as gpd
import pandas as pd

from config import (
    SA2_FILE, SA2_LAYER, GREATER_MELBOURNE,
    SEIFA_FILE, SEIFA_SHEET,
    HEAT_VEG_FILE, HEAT_VEG_LAYER,
)

from db import get_engine

def reset_tables(engine):
    with engine.begin() as conn:
        query = "TRUNCATE sa2, seifa, mesh_block_heat_veg, datasets, region_metrics"
        conn.execute(text(query))

def load_sa2(engine):
    gdf = gpd.read_file(
        SA2_FILE,
        layer=SA2_LAYER,
        where=f"GCCSA_CODE_2021 = '{GREATER_MELBOURNE}'",
        columns=["SA2_CODE_2021", "SA2_NAME_2021", "AREA_ALBERS_SQKM"],
    )

    gdf = gdf.rename(columns={
        "SA2_CODE_2021": "sa2_code", 
        "SA2_NAME_2021": "sa2_name", 
        "AREA_ALBERS_SQKM": "area_sqkm"})
    gdf = gdf.rename_geometry("geom")

    gdf.to_postgis("sa2", engine, if_exists="append", index=False)
    print(f"sa2: {len(gdf)} rows")

def load_seifa(engine):
    df = pd.read_excel(
        SEIFA_FILE,
        sheet_name=SEIFA_SHEET,
        header=None,
        skiprows=6,
        usecols="A,C,D,F,G,K,L",
        dtype={0: str},
    )
    df.columns = ["sa2_code", "population", "irsd_score",
                  "aus_rank", "aus_decile", "vic_rank", "vic_decile"]

    is_sa2_code = df["sa2_code"].str.fullmatch(r"\d{9}", na=False)
    df = df[is_sa2_code]

    sa2_table = pd.read_sql("SELECT sa2_code from sa2", engine)
    melbourne_codes = sa2_table["sa2_code"]

    is_melbourne = df["sa2_code"].isin(melbourne_codes)
    df = df[is_melbourne]

    df.to_sql("seifa", engine, if_exists="append", index=False)
    print(f"seifa: {len(df)} rows")

def load_mesh_block_heat_veg(engine):
    gdf = gpd.read_file(
        HEAT_VEG_FILE,
        layer=HEAT_VEG_LAYER,
        columns=["MB_CODE16", "LGA", "UHI18_M", "PERANYTREE", "PERTR03_10", "PERTR10_15", "PERTR15PL"],
    )

    gdf = gdf.rename(columns={
        "MB_CODE16": "mb_code", 
        "LGA": "lga", 
        "UHI18_M": "uhi",
        "PERANYTREE": "tree_pct",
        "PERTR03_10": "tree_3_10_pct",
        "PERTR10_15": "tree_10_15_pct",
        "PERTR15PL": "tree_15_plus_pct"})
    gdf = gdf.rename_geometry("geom")

    gdf.to_postgis("mesh_block_heat_veg", engine, if_exists="append", index=False)
    print(f"mesh_block_heat_veg: {len(gdf)} rows")

def load_datasets(engine):
    rows = [
        {
            "id": "abs_asgs_2021",
            "title": "ASGS 2021 Statistical Areas Level 2",
            "publisher": "Australian Bureau of Statistics",
            "licence": "CC BY 4.0",
            "source_url": "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files",
            "released": date(2021, 7, 20),
        },
        {
            "id": "abs_seifa_2021",
            "title": "SEIFA 2021 by SA2 (IRSD)",
            "publisher": "Australian Bureau of Statistics",
            "licence": "CC BY 4.0",
            "source_url": "https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/2021",
            "released": date(2023, 4, 27),
        },
        {
            "id": "vic_heat_vegetation_2018",
            "title": "Metropolitan Melbourne Urban Heat Islands and Urban Vegetation 2018",
            "publisher": "Department of Transport and Planning (Victoria)",
            "licence": "CC BY 4.0",
            "source_url": "https://discover.data.vic.gov.au/dataset/metropolitan-melbourne-urban-heat-islands-and-urban-vegetation-2018",
            "released": date(2019, 7, 6),
        },
    ]

    df = pd.DataFrame(rows)
    df.to_sql("datasets", engine, if_exists="append", index=False)
    print(f"datasets: {len(df)} rows")

if __name__ == "__main__":
    engine = get_engine()
    reset_tables(engine)
    load_sa2(engine)
    load_seifa(engine)
    load_mesh_block_heat_veg(engine)
    load_datasets(engine)