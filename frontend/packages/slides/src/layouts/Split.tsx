import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'
import { defaultField } from '../themes'

export function Split({ slide, theme, mode, selected, onSelect, onChange }: SlideProps) {
  return (
    <div className="layout-split">
      <div className="split-text">
        {slide.kicker ? (
          <TextBlock path="kicker" text={slide.kicker} className="kicker" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
        <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        {slide.body ? (
          <TextBlock path="body" text={slide.body} className="body" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
        {slide.button ? (
          <TextBlock path="button" text={slide.button} className="slide-button" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
      </div>
      <div className="split-field" style={{ background: slide.field || defaultField(theme) }} />
    </div>
  )
}
