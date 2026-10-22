import tomllib
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

with open(BACKEND_DIR / "sources.toml", "rb") as f:
    settings = tomllib.load(f)

RAW_DATA_DIR = PROJECT_ROOT / settings["paths"]["raw_data_dir"]

SA2_FILE = RAW_DATA_DIR / settings["sa2"]["file"]
SA2_LAYER = settings["sa2"]["layer"]
GREATER_MELBOURNE = settings["sa2"]["greater_melbourne"]

SEIFA_FILE = RAW_DATA_DIR / settings["seifa"]["file"]
SEIFA_SHEET = settings["seifa"]["sheet"]

HEAT_VEG_FILE = RAW_DATA_DIR / settings["heat_veg"]["file"]
HEAT_VEG_LAYER = settings["heat_veg"]["layer"]
