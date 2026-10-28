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

with open(BACKEND_DIR / "settings.toml", "rb") as f:
    analysis_settings = tomllib.load(f)

raw_weights = analysis_settings["risk_weights"]
if set(raw_weights) != {"heat", "canopy", "irsd"}:
    raise ValueError(f"settings.toml: risk_weights needs exactly heat, canopy and irsd, got {sorted(raw_weights)}")
if any(weight < 0 for weight in raw_weights.values()):
    raise ValueError(f"settings.toml: risk weights must not be negative, got {raw_weights}")
total_weight = sum(raw_weights.values())
if total_weight == 0:
    raise ValueError("settings.toml: at least one risk weight must be above 0")

RISK_WEIGHTS = {name: weight / total_weight for name, weight in raw_weights.items()}
