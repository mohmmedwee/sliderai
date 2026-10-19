import { BarChart } from '../charts/BarChart'
import { LineChart } from '../charts/LineChart'
import { PieChart } from '../charts/PieChart'
import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Chart({ slide, theme, mode, selected, onSelect, onChange }: SlideProps) {
  const chart = slide.chart
  const props = {
    chart: chart ?? { kind: 'bar' as const, labels: [], series: [] },
    accent: theme.tokens.accent,
    ink: theme.tokens.ink,
    paper: theme.tokens.paper,
  }
  return (
    <div className="layout-chart">
      <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      <div className="chart-slot">
        {chart?.kind === 'line' ? <LineChart {...props} /> : null}
        {chart?.kind === 'pie' || chart?.kind === 'donut' ? <PieChart {...props} /> : null}
        {!chart || chart.kind === 'bar' ? <BarChart {...props} /> : null}
      </div>
    </div>
  )
}
