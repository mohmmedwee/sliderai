import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Quote({ slide, theme, mode, selected, onSelect, onChange }: SlideProps) {
  return (
    <div className="layout-quote">
      <div className="quote-mark" aria-hidden="true">
        “
      </div>
      <TextBlock
        path="title"
        text={slide.title}
        className={theme.tokens.font === 'serif' ? 'quote-text serif' : 'quote-text'}
        mode={mode}
        selected={selected}
        onSelect={onSelect}
        onChange={onChange}
      />
      {slide.body ? (
        <TextBlock path="body" text={slide.body} className="caption" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      ) : null}
    </div>
  )
}
