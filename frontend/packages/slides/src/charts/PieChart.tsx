import { Legend } from './BarChart'
import { seriesColor } from './scale'
import type { ChartProps } from './types'

export function PieChart({ chart, accent, ink }: ChartProps) {
  const series = chart.series[0]
  const values = (series?.values ?? []).map((value) => value ?? 0)
  const total = values.reduce((sum, value) => sum + value, 0) || 1
  const outer = 180
  const inner = chart.kind === 'donut' ? outer * 0.55 : 0
  let angle = 0
  const slices = values.map((value) => {
    const sweep = (value / total) * 360
    const start = angle
    angle += sweep
    return { start, sweep }
  })
  return (
    <svg viewBox="0 0 1000 560" role="img">
      {chart.series.length > 1 ? <Legend chart={chart} accent={accent} ink={ink} /> : null}
      {slices.map((slice, index) => (
        <path
          key={chart.labels[index] ?? index}
          data-sweep={slice.sweep}
          d={arc(500, 300, outer, inner, slice.start, slice.start + slice.sweep)}
          fill={seriesColor(index, accent, ink)}
        />
      ))}
    </svg>
  )
}

function arc(cx: number, cy: number, outer: number, inner: number, start: number, end: number): string {
  const point = (deg: number, radius: number) => {
    const rad = ((deg - 90) * Math.PI) / 180
    return [cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)]
  }
  const large = end - start > 180 ? 1 : 0
  const [x1, y1] = point(start, outer)
  const [x2, y2] = point(end, outer)
  if (inner === 0) return `M ${cx} ${cy} L ${x1} ${y1} A ${outer} ${outer} 0 ${large} 1 ${x2} ${y2} Z`
  const [x3, y3] = point(end, inner)
  const [x4, y4] = point(start, inner)
  return `M ${x1} ${y1} A ${outer} ${outer} 0 ${large} 1 ${x2} ${y2} L ${x3} ${y3} A ${inner} ${inner} 0 ${large} 0 ${x4} ${y4} Z`
}
