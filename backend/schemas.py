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
    heat_quintile: int | None
    double_burden: bool | None
    irsd_score: float | None
    vic_decile: int | None
    population: int | None
    sources: list[Dataset]