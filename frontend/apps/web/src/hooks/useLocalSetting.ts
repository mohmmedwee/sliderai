import { useCallback, useState } from 'react'

/** Preferences the server does not store yet: theme, sidebar. */
export function useLocalSetting<T>(key: string, fallback: T) {
  const storageKey = `docu:${key}`

  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(storageKey)
      return raw === null ? fallback : (JSON.parse(raw) as T)
    } catch {
      return fallback
    }
  })

  const update = useCallback(
    (next: T) => {
      setValue(next)
      try {
        localStorage.setItem(storageKey, JSON.stringify(next))
      } catch {
        // Private browsing can refuse writes; the setting just won't persist.
      }
    },
    [storageKey],
  )

  return [value, update] as const
}
