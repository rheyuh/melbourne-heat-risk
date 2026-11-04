import type { RegionProperties } from "./types"

export const LAYERS = ["risk", "heat", "canopy", "disadvantage"] as const
export type Layer = (typeof LAYERS)[number]

interface LayerInfo {
  label: string
  value: (p: RegionProperties) => number | null
  reversed: boolean        // true when a LOWER value means more heat risk
  fixedBreaks?: number[]   // use these instead of calculated quintiles
}

export const LAYER_INFO: Record<Layer, LayerInfo> = {
  risk: { label: "Heat risk", value: (p) => p.risk_score, reversed: false },
  heat: { label: "Urban heat", value: (p) => p.heat_uhi, reversed: false },
  canopy: { label: "Tree canopy", value: (p) => p.canopy_pct, reversed: true },
  disadvantage: {
    label: "Disadvantage",
    value: (p) => p.vic_decile,
    reversed: true,
    fixedBreaks: [3, 5, 7, 9], // pairs deciles: 1–2, 3–4, 5–6, 7–8, 9–10
  },
}