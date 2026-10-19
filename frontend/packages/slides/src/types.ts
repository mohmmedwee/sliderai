import type { Schemas } from '@docu/api-types'

import type { Theme } from './themes'

export type Slide = Schemas['Slide']
export type { Theme }

export type FieldPath = 'kicker' | 'title' | 'body' | 'button' | `points.${number}`

export interface SlideProps {
  slide: Slide
  theme: Theme
  width?: number
  mode?: 'view' | 'edit'
  selected?: FieldPath | null
  onSelect?(path: FieldPath): void
  onChange?(path: FieldPath, value: string): void
  watermark?: boolean
}
