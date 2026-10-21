import os
from sqlalchemy import create_engine, text
from pathlib import Path
import geopandas as gpd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SA2_FILE = RAW_DATA_DIR / "abs_asgs_2021" / "ASGS_2021_Main_Structure_GDA2020.gpkg"
SA2_LAYER = "SA2_2021_AUST_GDA2020"
GREATER_MELBOURNE = "2GMEL"

def get_engine():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql+psycopg://{user}:{password}@localhost:{port}/{db}")

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

if __name__ == "__main__":
    engine = get_engine()
    load_sa2(engine)