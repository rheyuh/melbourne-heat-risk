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