export interface ChartSeries {
  name: string
  values: (number | null)[]
}

export interface ChartData {
  kind: 'bar' | 'line' | 'pie' | 'donut'
  labels: string[]
  series: ChartSeries[]
  unit?: string | null
}

export interface ChartProps {
  chart: ChartData
  accent: string
  ink: string
  paper: string
  dir?: 'ltr' | 'rtl'
  locale?: string
  digits?: 'latn' | 'arab'
}
