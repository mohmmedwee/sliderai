import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Title({ slide, mode, selected, onSelect, onChange }: SlideProps) {
  return (
    <div className="layout-title">
      <div className="title-stack">
        <div className="accent-bar" />
        {slide.kicker ? (
          <TextBlock path="kicker" text={slide.kicker} className="kicker" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
        <TextBlock path="title" text={slide.title} className="title-lg" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        {slide.body ? (
          <TextBlock path="body" text={slide.body} className="body" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
      </div>
    </div>
  )
}
