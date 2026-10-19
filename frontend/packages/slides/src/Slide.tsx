import { Chart } from './layouts/Chart'
import { Hero } from './layouts/Hero'
import { Points } from './layouts/Points'
import { Quote } from './layouts/Quote'
import { Split } from './layouts/Split'
import { Table } from './layouts/Table'
import { Title } from './layouts/Title'
import './slide.css'
import type { SlideProps } from './types'

const layouts = {
  hero: Hero,
  title: Title,
  points: Points,
  quote: Quote,
  split: Split,
  table: Table,
  chart: Chart,
}

export function Slide({
  slide,
  theme,
  width = 1280,
  mode = 'view',
  selected = null,
  onSelect,
  onChange,
  watermark = false,
}: SlideProps) {
  const Layout = layouts[slide.layout]
  const font =
    theme.tokens.font === 'serif'
      ? '"Noto Naskh Arabic", Fraunces, serif'
      : '"IBM Plex Sans Arabic", Inter, sans-serif'
  return (
    <div className="slide-frame" style={{ width, height: (width * 9) / 16 }}>
      <div
        className="slide-stage"
        role="region"
        aria-label={slide.title}
        style={{
          transform: `scale(${width / 1280})`,
          ['--s-bg' as string]: theme.tokens.bg,
          ['--s-paper' as string]: theme.tokens.paper,
          ['--s-ink' as string]: theme.tokens.ink,
          ['--s-accent' as string]: theme.tokens.accent,
          ['--s-font' as string]: font,
        }}
      >
        <Layout
          slide={slide}
          theme={theme}
          mode={mode}
          selected={selected}
          onSelect={onSelect}
          onChange={onChange}
        />
        {watermark ? <div className="watermark">Docu Builder</div> : null}
      </div>
    </div>
  )
}
