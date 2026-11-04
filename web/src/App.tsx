import { useEffect, useState } from "react"
import { GeoJSON, MapContainer, TileLayer, ZoomControl } from "react-leaflet"
import type { LatLngExpression, PathOptions } from "leaflet"
import type { Feature, Geometry } from "geojson"
import { fetchRegion, fetchRegions } from "./api"
import { LAYERS, LAYER_INFO, type Layer } from "./layers"
import { NO_DATA, YLORRD, classLabels, colourFor, quintileBreaks } from "./scale"
import type { RegionCollection, RegionDetail, RegionProperties } from "./types"

const MELBOURNE: LatLngExpression = [-37.8136, 144.9631]
const DOUBLE_BURDEN_COLOUR = "#1f4e9c"

function App() {
  const [regions, setRegions] = useState<RegionCollection | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [layer, setLayer] = useState<Layer>("risk")
  const [selectedCode, setSelectedCode] = useState<string | null>(null)

  useEffect(() => {
    fetchRegions()
      .then(setRegions)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  const [detail, setDetail] = useState<RegionDetail | null>(null)
  const [detailError, setDetailError] = useState<{ code: string; message: string } | null>(null)

  // Load the selected region's details whenever the selection changes
  useEffect(() => {
    if (selectedCode === null) return
    let ignore = false
    fetchRegion(selectedCode)
      .then((d) => {
        if (!ignore) setDetail(d)
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setDetailError({ code: selectedCode, message: err instanceof Error ? err.message : String(err) })
        }
      })
    return () => {
      ignore = true
    }
  }, [selectedCode])

  // Only show results for the region that's selected now, not an earlier one
  const shownDetail = detail?.sa2_code === selectedCode ? detail : null
  const shownError = detailError?.code === selectedCode ? detailError.message : null

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

  // Only the regions flagged as double burden, for the outline layer
  const doubleBurden: RegionCollection | null = regions
    ? { ...regions, features: regions.features.filter((f) => f.properties.double_burden === true) }
    : null

  return (
    <>
      {error && <div className="error">Couldn't load regions: {error}</div>}
      {selectedCode && (
        <aside className="region-card">
          <button className="close" onClick={() => setSelectedCode(null)} aria-label="Close details">
            ✕
          </button>
          <h2>{shownDetail ? shownDetail.sa2_name : selectedCode}</h2>
          {shownError && <p className="card-error">Couldn't load details: {shownError}</p>}
          {!shownDetail && !shownError && <p className="card-loading">Loading…</p>}
        </aside>
      )}
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
            <div className="legend-row">
              <span className="swatch swatch-outline" />
              Double burden
            </div>
          </div>
        )}
      </div>
      <MapContainer center={MELBOURNE} zoom={11} className="map" zoomControl={false}>
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <ZoomControl position="bottomright" />
        {regions && (
          <GeoJSON
            data={regions}
            style={styleRegion}
            eventHandlers={{
              click: (e) => {
                const feature = e.propagatedFrom.feature as Feature<Geometry, RegionProperties>
                setSelectedCode(feature.properties.sa2_code)
              },
            }}
          />
        )}
        {doubleBurden && (
          <GeoJSON
            data={doubleBurden}
            style={{ color: DOUBLE_BURDEN_COLOUR, weight: 2.5, fill: false }}
            interactive={false}
          />
        )}
      </MapContainer>
    </>
  )
}

export default App;