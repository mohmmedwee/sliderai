import '@testing-library/jest-dom/vitest'
import { fireEvent, render } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { Slide } from '../src/Slide'
import type { FieldPath } from '../src/types'
import { getTheme } from '../src/themes'
import { ar, en } from './fixtures'

const theme = getTheme('paper')
const expected: Record<string, string[]> = {
  hero: ['kicker', 'title', 'body', 'button'],
  title: ['kicker', 'title', 'body'],
  points: ['title', 'points.0', 'points.1'],
  quote: ['title', 'body'],
  split: ['kicker', 'title', 'body', 'button'],
  table: ['title'],
  chart: ['title'],
}

describe('Slide', () => {
  it('renders each layout in English and Arabic', () => {
    for (const sample of [...Object.values(en), ...Object.values(ar)]) {
      const view = render(<Slide slide={sample} theme={theme} />)
      for (const field of expected[sample.layout]!) {
        const node = view.container.querySelector(`[data-field="${field}"]`)
        expect(node, `${sample.id} ${field}`).not.toBeNull()
        expect(node).toHaveAttribute('dir', 'auto')
      }
      view.unmount()
    }
  })

  it('marks a title that still overflows after fitting', () => {
    const scroll = vi.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockReturnValue(400)
    const client = vi.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockReturnValue(20)
    const view = render(<Slide slide={{ ...en.title, title: 'A'.repeat(140) }} theme={theme} />)
    expect(view.container.querySelector('[data-field="title"]')).toHaveAttribute('data-overflow', 'true')
    view.unmount()
    scroll.mockRestore()
    client.mockRestore()
  })

  it('selects a block and reports the edited text', () => {
    const onChange = vi.fn()
    function Harness() {
      const [selected, setSelected] = useState<FieldPath | null>(null)
      return (
        <Slide
          slide={en.title}
          theme={theme}
          mode="edit"
          selected={selected}
          onSelect={setSelected}
          onChange={onChange}
        />
      )
    }
    const view = render(<Harness />)
    fireEvent.click(view.container.querySelector('[data-field="title"]')!)
    const title = view.container.querySelector('[data-field="title"]')!
    expect(title).toHaveAttribute('contenteditable', 'plaintext-only')
    title.textContent = 'Changed'
    fireEvent.blur(title)
    expect(onChange).toHaveBeenCalledWith('title', 'Changed')
  })
})
