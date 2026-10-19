import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'
import { defaultField } from '../themes'

export function Hero({ slide, theme, mode, selected, onSelect, onChange }: SlideProps) {
  return (
    <div className="layout-hero">
      <div className="hero-field" style={{ background: slide.field || defaultField(theme) }} />
      <div className="hero-panel">
        {slide.kicker ? (
          <TextBlock path="kicker" text={slide.kicker} className="kicker" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
        <TextBlock path="title" text={slide.title} className="title-lg" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        {slide.body ? (
          <TextBlock path="body" text={slide.body} className="body" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
        {slide.button ? (
          <TextBlock path="button" text={slide.button} className="slide-button" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
        ) : null}
      </div>
    </div>
  )
}
