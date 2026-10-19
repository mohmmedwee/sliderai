import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Chart({ slide, mode, selected, onSelect, onChange }: SlideProps) {
  return (
    <div className="layout-chart">
      <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      <div className="chart-slot" data-chart={slide.chart?.kind ?? 'bar'} />
    </div>
  )
}
