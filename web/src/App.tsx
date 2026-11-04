import { useEffect, useState } from "react"
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet"
import type { LatLngExpression, PathOptions } from "leaflet"
import type { Feature, Geometry } from "geojson"
import { fetchRegions } from "./api"
import { colourFor, quintileBreaks } from "./scale"
import type { RegionCollection, RegionProperties } from "./types"

const MELBOURNE: LatLngExpression = [-37.8136, 144.9631]

function App() {
  const [regions, setRegions] = useState<RegionCollection | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRegions()
      .then(setRegions)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  const riskBreaks = regions
    ? quintileBreaks(regions.features.map((f) => f.properties.risk_score))
    : []

  function styleRegion(feature?: Feature<Geometry, RegionProperties>): PathOptions {
    return {
      fillColor: colourFor(feature?.properties.risk_score ?? null, riskBreaks),
      fillOpacity: 0.7,
      color: "#555",
      weight: 0.5,
    }
  }

  return (
    <>
      {error && <div className="error">Couldn't load regions: {error}</div>}
      <MapContainer center={MELBOURNE} zoom={11} className="map">
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {regions && (
          <GeoJSON data={regions} style={styleRegion} />
        )}
      </MapContainer>
    </>
  )
}

export default App;