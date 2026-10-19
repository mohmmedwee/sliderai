import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Points({ slide, mode, selected, onSelect, onChange }: SlideProps) {
  const points = slide.points ?? []
  return (
    <div className="layout-points">
      <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      <div className={points.length > 4 ? 'points two' : 'points'}>
        {points.map((point, index) => (
          <TextBlock
            key={`${index}-${point}`}
            path={`points.${index}`}
            text={point}
            className="point"
            mode={mode}
            selected={selected}
            onSelect={onSelect}
            onChange={onChange}
          />
        ))}
      </div>
    </div>
  )
}
