import { useEffect } from 'react'

import { useLocalSetting } from '@/hooks/useLocalSetting'

export type Theme = 'light' | 'dark'

/** Theme is a class on <html>, matching the dark variant in the stylesheet. */
export function useTheme() {
  const [theme, setTheme] = useLocalSetting<Theme>('theme', 'light')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return { theme, setTheme }
}
