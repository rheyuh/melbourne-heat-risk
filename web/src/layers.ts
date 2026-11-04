import type { RegionProperties } from "./types"

export const LAYERS = ["risk", "heat", "canopy", "disadvantage"] as const
export type Layer = (typeof LAYERS)[number]

interface LayerInfo {
  label: string
  value: (p: RegionProperties) => number | null
  reversed: boolean        // true when a LOWER value means more heat risk
  fixedBreaks?: number[]   // use these instead of calculated quintiles
  format: (n: number) => string   // how a break value is shown in the legend
  fixedLabels?: string[]          // legend text per class, when breaks aren't real values
  note?: string                   // one-line explanation shown in the legend
}

export const LAYER_INFO: Record<Layer, LayerInfo> = {
  risk: {
    label: "Heat risk",
    value: (p) => p.risk_score,
    reversed: false,
    format: (n) => n.toFixed(2),
    note: "Heat risk combines urban heat, lack of tree canopy and socio-economic disadvantage, weighted equally.",
  },
  heat: {
    label: "Urban heat",
    value: (p) => p.heat_uhi,
    reversed: false,
    format: (n) => `${n.toFixed(1)} °C`,
  },
  canopy: {
    label: "Tree canopy",
    value: (p) => p.canopy_pct,
    reversed: true,
    format: (n) => `${n.toFixed(1)}%`,
  },
  disadvantage: {
    label: "Disadvantage",
    value: (p) => p.vic_decile,
    reversed: true,
    fixedBreaks: [3, 5, 7, 9], // pairs deciles: 1–2, 3–4, 5–6, 7–8, 9–10
    format: (n) => String(n),
    fixedLabels: ["Deciles 1–2", "Deciles 3–4", "Deciles 5–6", "Deciles 7–8", "Deciles 9–10"],
  },
}