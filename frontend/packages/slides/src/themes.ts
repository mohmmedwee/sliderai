import data from './generated/themes.json'

export interface ThemeTokens {
  bg: string
  paper: string
  ink: string
  accent: string
  tone: 'light' | 'dark'
  font: 'sans' | 'serif'
}

export interface Theme {
  id: string
  name: string
  tokens: ThemeTokens
  tags: string[]
}

export const THEMES = data as Theme[]

export function getTheme(id: string): Theme {
  return THEMES.find((theme) => theme.id === id) ?? THEMES.find((theme) => theme.id === 'paper')!
}

export function defaultField(theme: Theme): string {
  return `linear-gradient(135deg, ${theme.tokens.accent}, ${theme.tokens.bg})`
}
