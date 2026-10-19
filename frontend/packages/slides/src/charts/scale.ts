export function niceTicks(min: number, max: number, count = 5): number[] {
  const span = niceNum(max - min || 1, false)
  const step = niceNum(span / (count - 1), true)
  const start = Math.floor(min / step) * step
  const end = Math.ceil(max / step) * step
  const ticks: number[] = []
  for (let value = start; value <= end + step / 2; value += step) {
    ticks.push(Math.round(value * 1e6) / 1e6)
  }
  return ticks
}

function niceNum(range: number, round: boolean): number {
  const exp = Math.floor(Math.log10(range))
  const frac = range / 10 ** exp
  let nice = 10
  if (round) {
    if (frac < 1.5) nice = 1
    else if (frac < 3) nice = 2
    else if (frac < 7) nice = 5
  } else if (frac <= 1) nice = 1
  else if (frac <= 2) nice = 2
  else if (frac <= 5) nice = 5
  return nice * 10 ** exp
}

export function formatValue(
  value: number,
  unit: string | null | undefined,
  locale: string,
  digits: 'latn' | 'arab',
): string {
  const text = new Intl.NumberFormat(locale, {
    numberingSystem: digits,
    maximumFractionDigits: 2,
  }).format(value)
  return unit ? `${text} ${unit}` : text
}

export function seriesColor(index: number, accent: string, ink: string): string {
  const mix = [0, 0.25, 0.45, 0.6, 0.75, 0.85][index] ?? 0.85
  return mixHex(accent, ink, mix)
}

function mixHex(from: string, to: string, amount: number): string {
  const left = rgb(from)
  const right = rgb(to)
  const mixed = left.map((channel, index) => Math.round(channel * (1 - amount) + right[index]! * amount))
  return `#${mixed.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`
}

function rgb(hex: string): [number, number, number] {
  const value = hex.replace('#', '')
  const full = value.length === 3 ? value.split('').map((part) => part + part).join('') : value
  return [parseInt(full.slice(0, 2), 16), parseInt(full.slice(2, 4), 16), parseInt(full.slice(4, 6), 16)]
}
