import { formatValue, niceTicks, seriesColor } from './scale'
import type { ChartProps } from './types'

export function BarChart({ chart, accent, ink, paper, dir = 'ltr', locale = 'en', digits = 'latn' }: ChartProps) {
  const labels = chart.labels
  const series = chart.series
  const numbers = series.flatMap((item) => item.values.filter((value): value is number => value != null))
  const ticks = niceTicks(Math.min(0, ...numbers, 0), Math.max(0, ...numbers, 1))
  const top = ticks[ticks.length - 1] ?? 1
  const bottom = ticks[0] ?? 0
  const plot = { x: dir === 'rtl' ? 40 : 70, y: 36, w: 890, h: 470 }
  const group = plot.w / Math.max(labels.length, 1)
  const yFor = (value: number) => plot.y + plot.h - ((value - bottom) / (top - bottom || 1)) * plot.h
  return (
    <svg viewBox="0 0 1000 560" role="img">
      <rect width="1000" height="560" fill={paper} />
      {chart.series.length > 1 ? <Legend chart={chart} accent={accent} ink={ink} /> : null}
      {ticks.map((tick) => (
        <text key={tick} x={dir === 'rtl' ? 960 : 60} y={yFor(tick)} textAnchor={dir === 'rtl' ? 'start' : 'end'} fill={ink} fontSize="18">
          {formatValue(tick, null, locale, digits)}
        </text>
      ))}
      {labels.map((label, index) => {
        const visualIndex = dir === 'rtl' ? labels.length - 1 - index : index
        const x = plot.x + visualIndex * group
        return (
          <g key={label}>
            <text data-label={label} x={x + group / 2} y={540} textAnchor="middle" fill={ink} fontSize="18" dir="auto">
              {label}
            </text>
            {series.map((item, seriesIndex) => {
              const value = item.values[index] ?? 0
              const barW = group / (series.length + 1)
              const barX = x + barW * seriesIndex + barW / 2
              const y = yFor(Math.max(value, 0))
              const height = Math.abs(yFor(value) - yFor(0))
              return (
                <rect
                  key={item.name}
                  x={barX}
                  y={y}
                  width={barW * 0.8}
                  height={height}
                  fill={seriesColor(seriesIndex, accent, ink)}
                />
              )
            })}
          </g>
        )
      })}
    </svg>
  )
}

export function Legend({
  chart,
  accent,
  ink,
}: {
  chart: ChartProps['chart']
  accent: string
  ink: string
}) {
  return (
    <g>
      {chart.series.map((item, index) => (
        <text key={item.name} x={80 + index * 160} y={24} fill={ink} fontSize="18" dir="auto">
          <tspan fill={seriesColor(index, accent, ink)}>●</tspan> {item.name}
        </text>
      ))}
    </g>
  )
}
