import type { FeatureCollection, MultiPolygon, Polygon } from "geojson"

// Mirrors backend/schemas.py Dataset
export interface Dataset {
  id: string
  title: string
  publisher: string
  licence: string
  source_url: string | null
}

// Mirrors backend/schemas.py RegionDetail (GET /regions/{sa2_code} and /regions/at)
export interface RegionDetail {
  sa2_code: string
  sa2_name: string
  area_sqkm: number | null
  heat_uhi: number | null
  canopy_pct: number | null
  covered_fraction: number | null
  heat_scaled: number | null
  canopy_scaled: number | null
  irsd_scaled: number | null
  risk_score: number | null
  risk_rank: number | null       // 1 = highest risk; null when unscored
  ranked_count: number | null    // the "of N"
  heat_quintile: number | null
  double_burden: boolean | null
  irsd_score: number | null
  vic_decile: number | null
  population: number | null
  sources: Dataset[]
}

// Mirrors backend/schemas.py Hotspot (GET /hotspots)
export interface Hotspot {
  rank: number
  sa2_code: string
  sa2_name: string
  risk_score: number
  double_burden: boolean | null
  heat_uhi: number
  canopy_pct: number
  vic_decile: number | null
}

// Mirrors the properties built by backend/formats.py to_feature (GET /regions)
export interface RegionProperties {
  sa2_code: string
  sa2_name: string
  risk_score: number | null
  double_burden: boolean | null
  heat_uhi: number | null
  canopy_pct: number | null
  vic_decile: number | null
}

export type RegionCollection = FeatureCollection<Polygon | MultiPolygon, RegionProperties>