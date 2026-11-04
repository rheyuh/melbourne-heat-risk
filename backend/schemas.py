"""Response shapes for the API. Knows fields and types, not SQL or HTTP."""
from pydantic import BaseModel

class Dataset(BaseModel):
    id: str
    title: str
    publisher: str
    licence: str
    source_url: str | None

class RegionDetail(BaseModel):
    sa2_code: str
    sa2_name: str
    area_sqkm: float | None
    heat_uhi: float | None
    canopy_pct: float | None
    covered_fraction: float | None
    heat_scaled: float | None
    canopy_scaled: float | None
    irsd_scaled: float | None
    risk_score: float | None
    risk_rank: int | None       # 1 = highest risk; None when the region has no risk score
    ranked_count: int | None    # how many regions have a rank (the "of N")
    heat_quintile: int | None
    double_burden: bool | None
    irsd_score: float | None
    vic_decile: int | None
    population: int | None
    sources: list[Dataset]

class Hotspot(BaseModel):
    rank: int
    sa2_code: str
    sa2_name: str
    risk_score: float
    double_burden: bool | None
    heat_uhi: float
    canopy_pct: float
    vic_decile: int | None

# Columns for /regions.csv: every RegionDetail field except the nested sources list
# and ranked_count (the same number on every row).
REGION_CSV_COLUMNS = []
for name in RegionDetail.model_fields:
    if name not in ("sources", "ranked_count"):
        REGION_CSV_COLUMNS.append(name)