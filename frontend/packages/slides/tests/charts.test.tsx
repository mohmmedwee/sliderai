import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { BarChart } from '../src/charts/BarChart'
import { PieChart } from '../src/charts/PieChart'
import { formatValue, niceTicks } from '../src/charts/scale'

const chart = {
  kind: 'bar' as const,
  labels: ['A', 'B'],
  series: [{ name: 'One', values: [10, 20] }],
  unit: null,
}

describe('charts', () => {
  it('builds nice ticks for 0 to 97', () => {
    expect(niceTicks(0, 97)).toEqual([0, 20, 40, 60, 80, 100])
  })

  it('formats values with arabic digits', () => {
    expect(formatValue(12, 'kg', 'ar', 'arab')).toContain('١')
  })

  it('flips category order in rtl', () => {
    const ltr = render(<BarChart chart={chart} accent="#1f3fff" ink="#0d1b4c" paper="#ffffff" />)
    const ltrX = [...ltr.container.querySelectorAll('[data-label]')].map((node) => Number(node.getAttribute('x')))
    ltr.unmount()
    const rtl = render(<BarChart chart={chart} accent="#1f3fff" ink="#0d1b4c" paper="#ffffff" dir="rtl" />)
    const rtlX = [...rtl.container.querySelectorAll('[data-label]')].map((node) => Number(node.getAttribute('x')))
    expect(ltrX[0]).toBeLessThan(ltrX[1]!)
    expect(rtlX[0]).toBeGreaterThan(rtlX[1]!)
  })

  it('sums pie slices to 360 degrees', () => {
    const view = render(
      <PieChart
        chart={{ kind: 'pie', labels: ['A', 'B', 'C'], series: [{ name: 'S', values: [1, 1, 2] }] }}
        accent="#1f3fff"
        ink="#0d1b4c"
        paper="#ffffff"
      />,
    )
    const sweep = [...view.container.querySelectorAll('[data-sweep]')].reduce(
      (sum, node) => sum + Number(node.getAttribute('data-sweep')),
      0,
    )
    expect(sweep).toBeCloseTo(360)
  })
})