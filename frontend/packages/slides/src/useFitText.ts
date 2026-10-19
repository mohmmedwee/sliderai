import { useLayoutEffect, type RefObject } from 'react'

export function useFitText(ref: RefObject<HTMLElement | null>, options: { min: number }): void {
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const base = Number.parseFloat(getComputedStyle(el).fontSize) || 48
    const floor = base * options.min
    let size = base
    el.style.fontSize = `${size}px`
    while (el.scrollHeight > el.clientHeight && size > floor + 0.5) {
      size = Math.max(floor, size * 0.9)
      el.style.fontSize = `${size}px`
    }
    if (el.scrollHeight > el.clientHeight) el.dataset.overflow = 'true'
    else delete el.dataset.overflow
  })
}
