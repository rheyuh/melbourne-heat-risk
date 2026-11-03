import { useEffect, useState } from "react"
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet"
import type { LatLngExpression } from "leaflet"
import { fetchRegions } from "./api"
import type { RegionCollection } from "./types"

const MELBOURNE: LatLngExpression = [-37.8136, 144.9631]

function App() {
  const [regions, setRegions] = useState<RegionCollection | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRegions()
      .then(setRegions)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  return (
    <>
      {error && <div className="error">Couldn't load regions: {error}</div>}
      <MapContainer center={MELBOURNE} zoom={11} className="map">
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {regions && (
          <GeoJSON data={regions} style={{ color: "#555", weight: 1, fillOpacity: 0.1 }} />
        )}
      </MapContainer>
    </>
  )
}

export default App;