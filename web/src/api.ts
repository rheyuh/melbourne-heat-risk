import type { Dataset, Hotspot, RegionCollection, RegionDetail } from "./types"

const API = "/api"

// An HTTP error from the API, keeping the status so callers can tell 404 from 503
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`)
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      if (typeof body?.detail === "string") detail = body.detail
    } catch {
      // Body wasn't JSON (e.g. a proxy error page), so keep the status text
    }
    throw new ApiError(response.status, `${response.status} ${detail}`)
  }
  return (await response.json()) as T
}

export function fetchRegions() {
  return getJson<RegionCollection>("/regions")
}

export function fetchRegion(sa2Code: string) {
  return getJson<RegionDetail>(`/regions/${encodeURIComponent(sa2Code)}`)
}

// Returns null when the point is outside Greater Melbourne (the API's 404)
export async function fetchRegionAt(lat: number, lon: number): Promise<RegionDetail | null> {
  const query = new URLSearchParams({ lat: String(lat), lon: String(lon) })
  try {
    return await getJson<RegionDetail>(`/regions/at?${query}`)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function fetchHotspots(top = 10) {
  return getJson<Hotspot[]>(`/hotspots?top=${top}`)
}

export function fetchDatasets() {
  return getJson<Dataset[]>("/datasets")
}

export const REGIONS_CSV_URL = `${API}/regions.csv`