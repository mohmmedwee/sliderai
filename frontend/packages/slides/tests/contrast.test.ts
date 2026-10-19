import { describe, expect, it } from 'vitest'

import { THEMES } from '../src/themes'

function channel(value: number): number {
  if (value <= 0.04045) return value / 12.92
  return ((value + 0.055) / 1.055) ** 2.4
}

function contrast(left: string, right: string): number {
  const luminance = (color: string) => {
    const red = Number.parseInt(color.slice(1, 3), 16) / 255
    const green = Number.parseInt(color.slice(3, 5), 16) / 255
    const blue = Number.parseInt(color.slice(5, 7), 16) / 255
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)
  }
  const [lighter, darker] = [luminance(left), luminance(right)].sort((a, b) => b - a)
  return (lighter! + 0.05) / (darker! + 0.05)
}

describe('theme contrast', () => {
  it('keeps ink on paper at 4.5 and paper on accent at 3', () => {
    expect(THEMES).toHaveLength(26)
    for (const theme of THEMES) {
      expect(contrast(theme.tokens.ink, theme.tokens.paper)).toBeGreaterThanOrEqual(4.5)
      expect(contrast(theme.tokens.paper, theme.tokens.accent)).toBeGreaterThanOrEqual(3)
    }
  })
})
