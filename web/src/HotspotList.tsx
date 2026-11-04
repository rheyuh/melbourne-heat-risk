import { REGIONS_CSV_URL } from "./api"
import { LAYER_INFO } from "./layers"
import type { Hotspot } from "./types"

interface Props {
  hotspots: Hotspot[] | null
  error: string | null
  onSelect: (sa2Code: string) => void
}

export function HotspotList({ hotspots, error, onSelect }: Props) {
  return (
    <>
      <h2>Top 10 heat risk hotspots</h2>
      {error && <p className="card-error">Couldn't load hotspots: {error}</p>}
      {!hotspots && !error && <p className="card-loading">Loading…</p>}
      {hotspots && (
        <ol className="hotspots">
          {hotspots.map((h) => (
            <li key={h.sa2_code}>
              <button type="button" onClick={() => onSelect(h.sa2_code)}>
                <span>{h.sa2_name}</span>
                <span className="hotspot-score">{LAYER_INFO.risk.format(h.risk_score)}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
      <a className="download" href={REGIONS_CSV_URL} download>
        Download all regions (CSV)
      </a>
    </>
  )
}
