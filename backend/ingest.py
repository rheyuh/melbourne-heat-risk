import os
from sqlalchemy import create_engine, text
from pathlib import Path
import geopandas as gpd
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SA2_FILE = RAW_DATA_DIR / "abs_asgs_2021" / "ASGS_2021_Main_Structure_GDA2020.gpkg"
SA2_LAYER = "SA2_2021_AUST_GDA2020"
GREATER_MELBOURNE = "2GMEL"

SEIFA_FILE = RAW_DATA_DIR / "abs_seifa_2021" / "Statistical Area Level 2, Indexes, SEIFA 2021.xlsx"

def get_engine():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql+psycopg://{user}:{password}@localhost:{port}/{db}")

def reset_tables(engine):
    with engine.begin() as conn:
        query = "TRUNCATE sa2, seifa, heat_veg_raw, datasets"
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
        sheet_name="Table 2",
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

if __name__ == "__main__":
    engine = get_engine()
    reset_tables(engine)
    load_sa2(engine)
    load_seifa(engine)