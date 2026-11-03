// Four values that split `values` into five equal-sized groups (quintiles).
// Nulls are skipped: regions with no data are drawn grey, not put in a class.
export function quintileBreaks(values: (number | null)[]): number[] {
  // 1. Keep only the numbers (0 stays; only null is dropped)
  const nums = values.filter((v): v is number => v !== null)

  // 2. Nothing to split, so no breaks
  if (nums.length === 0) return []

  // 3. Sort a copy from smallest to largest (numerically, not as text)
  const sorted = [...nums].sort((a, b) => a - b)

  // 4. Take the value 1/5, 2/5, 3/5 and 4/5 of the way through the list
  const breaks: number[] = []
  for (let k = 1; k <= 4; k++) {
    breaks.push(sorted[Math.floor((k * sorted.length) / 5)])
  }
  return breaks
}

// ColorBrewer YlOrRd, 5 classes: lightest = lowest heat risk, darkest = highest
export const YLORRD = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
export const NO_DATA = "#cccccc"

// Which of the five classes (0–4) a value falls in, given four breaks.
// A value equal to a break goes in the class above it.
export function classIndex(value: number, breaks: number[]): number {
  let i = 0
  while (i < breaks.length && value >= breaks[i]) i++
  return i
}

// Fill colour for one region: grey when there's no data, otherwise its class's colour
export function colourFor(value: number | null, breaks: number[]): string {
  if (value === null) return NO_DATA
  return YLORRD[classIndex(value, breaks)]
}