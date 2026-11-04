import { useEffect, useState } from "react"
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet"
import type { LatLngExpression, PathOptions } from "leaflet"
import type { Feature, Geometry } from "geojson"
import { fetchRegions } from "./api"
import { LAYERS, LAYER_INFO, type Layer } from "./layers"
import { NO_DATA, YLORRD, classLabels, colourFor, quintileBreaks } from "./scale"
import type { RegionCollection, RegionProperties } from "./types"

const MELBOURNE: LatLngExpression = [-37.8136, 144.9631]

function App() {
  const [regions, setRegions] = useState<RegionCollection | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [layer, setLayer] = useState<Layer>("risk")

  useEffect(() => {
    fetchRegions()
      .then(setRegions)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  const info = LAYER_INFO[layer]
  const breaks = 
    info.fixedBreaks ??
    (regions ? quintileBreaks(regions.features.map((f) => info.value(f.properties))) : [])

  function styleRegion(feature?: Feature<Geometry, RegionProperties>): PathOptions {
    const value = feature ? info.value(feature.properties) : null
    return {
      fillColor: colourFor(value, breaks, info.reversed),
      fillOpacity: 0.7,
      color: "#555",
      weight: 0.5,
    }
  }

  // Legend rows, darkest (most heat risk) first
  const labels = info.fixedLabels ?? (breaks.length > 0 ? classLabels(breaks, info.format) : [])
  const legend = labels
    .map((text, i) => ({ text, colourIndex: info.reversed ? YLORRD.length - 1 - i : i }))
    .sort((a, b) => b.colourIndex - a.colourIndex)

  return (
    <>
      {error && <div className="error">Couldn't load regions: {error}</div>}
      <div className="panel">
        <fieldset>
          <legend>Show</legend>
          {LAYERS.map((l) => (
            <label key={l}>
              <input
                type="radio"
                name="layer"
                value={l}
                checked={layer === l}
                onChange={() => setLayer(l)}
              />
              {LAYER_INFO[l].label}
            </label>
          ))}
        </fieldset>
        {legend.length > 0 && (
          <div className="legend">
            <div className="legend-title">{info.label}</div>
            {info.note && <div className="legend-note">{info.note}</div>}
            <div className="legend-hint">Deep red indicates more heat risk</div>
            {legend.map((row) => (
              <div key={row.text} className="legend-row">
                <span className="swatch" style={{ background: YLORRD[row.colourIndex] }} />
                {row.text}
              </div>
            ))}
            <div className="legend-row">
              <span className="swatch" style={{ background: NO_DATA }} />
              No data
            </div>
          </div>
        )}
      </div>
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