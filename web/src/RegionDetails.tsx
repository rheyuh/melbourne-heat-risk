import { LAYER_INFO } from "./layers"
import type { RegionDetail } from "./types"

// "No data" for missing values, otherwise the value in its display format
function show(value: number | null, format: (n: number) => string): string {
  return value === null ? "No data" : format(value)
}

export function RegionDetails({ detail }: { detail: RegionDetail }) {
  const rows: [string, string][] = [
    ["Heat risk", show(detail.risk_score, LAYER_INFO.risk.format)],
    ["Urban heat", show(detail.heat_uhi, LAYER_INFO.heat.format)],
    ["Tree canopy", show(detail.canopy_pct, LAYER_INFO.canopy.format)],
    ["Disadvantage", show(detail.vic_decile, (n) => `Decile ${n} (1 = most disadvantaged)`)],
    ["Population", show(detail.population, (n) => n.toLocaleString("en-AU"))],
    ["Area", show(detail.area_sqkm, (n) => `${n.toFixed(1)} km²`)],
  ]

  return (
    <>
      <p className="rank">
        {detail.risk_rank !== null && detail.ranked_count !== null
          ? `Rank ${detail.risk_rank} of ${detail.ranked_count} for heat risk`
          : "Not ranked (no risk score)"}
      </p>
      {detail.double_burden && <p className="badge">Double burden</p>}

      <dl className="metrics">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>

      <h3>Data sources</h3>
      <ul className="sources">
        {detail.sources.map((s) => (
          <li key={s.id}>
            {s.source_url ? (
              <a href={s.source_url} target="_blank" rel="noreferrer">
                {s.title}
              </a>
            ) : (
              s.title
            )}
            <span className="source-meta">
              {s.publisher} · {s.licence}
            </span>
          </li>
        ))}
      </ul>
    </>
  )
}
