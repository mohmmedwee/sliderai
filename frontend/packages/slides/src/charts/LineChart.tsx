import { Legend } from './BarChart'
import { niceTicks, seriesColor } from './scale'
import type { ChartProps } from './types'

export function LineChart({ chart, accent, ink, dir = 'ltr' }: ChartProps) {
  const labels = chart.labels
  const series = chart.series
  const numbers = series.flatMap((item) => item.values.filter((value): value is number => value != null))
  const ticks = niceTicks(Math.min(0, ...numbers, 0), Math.max(0, ...numbers, 1))
  const top = ticks[ticks.length - 1] ?? 1
  const bottom = ticks[0] ?? 0
  const plot = { x: dir === 'rtl' ? 40 : 70, y: 36, w: 890, h: 470 }
  const step = plot.w / Math.max(labels.length - 1, 1)
  const yFor = (value: number) => plot.y + plot.h - ((value - bottom) / (top - bottom || 1)) * plot.h
  return (
    <svg viewBox="0 0 1000 560" role="img">
      {chart.series.length > 1 ? <Legend chart={chart} accent={accent} ink={ink} /> : null}
      {labels.map((label, index) => {
        const visualIndex = dir === 'rtl' ? labels.length - 1 - index : index
        return (
          <text key={label} data-label={label} x={plot.x + visualIndex * step} y={540} textAnchor="middle" fill={ink} fontSize="18" dir="auto">
            {label}
          </text>
        )
      })}
      {series.map((item, seriesIndex) => {
        const points = item.values
          .map((value, index) => {
            const visualIndex = dir === 'rtl' ? labels.length - 1 - index : index
            return `${plot.x + visualIndex * step},${yFor(value ?? 0)}`
          })
          .join(' ')
        return <polyline key={item.name} points={points} fill="none" stroke={seriesColor(seriesIndex, accent, ink)} strokeWidth="4" />
      })}
    </svg>
  )
}
