import { useRef } from 'react'

import type { FieldPath, SlideProps } from './types'
import { useFitText } from './useFitText'

export function TextBlock({
  path,
  text,
  className,
  mode,
  selected,
  onSelect,
  onChange,
}: {
  path: FieldPath
  text: string
  className?: string
  mode: SlideProps['mode']
  selected: SlideProps['selected']
  onSelect: SlideProps['onSelect']
  onChange: SlideProps['onChange']
}) {
  const ref = useRef<HTMLDivElement>(null)
  useFitText(ref, { min: 0.7 })
  const editing = mode === 'edit' && selected === path
  const latin = !/[\u0600-\u06FF]/.test(text)
  return (
    <div
      ref={ref}
      dir="auto"
      data-field={path}
      className={[className, latin && className?.includes('kicker') ? 'upper' : '', mode === 'edit' ? 'slide-hover' : '']
        .filter(Boolean)
        .join(' ')}
      contentEditable={editing ? 'plaintext-only' : undefined}
      suppressContentEditableWarning
      role={editing ? 'textbox' : undefined}
      onClick={(event) => {
        if (mode !== 'edit') return
        event.stopPropagation()
        onSelect?.(path)
      }}
      onBlur={(event) => {
        if (!editing) return
        onChange?.(path, event.currentTarget.textContent ?? '')
      }}
    >
      {text}
    </div>
  )
}
