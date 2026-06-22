import { useCallback, useSyncExternalStore } from 'react'

type Theme = 'light' | 'dark'

const listeners = new Set<() => void>()

function getTheme(): Theme {
  return (document.documentElement.getAttribute('data-theme') as Theme) || 'dark'
}

function setTheme(t: Theme) {
  document.documentElement.setAttribute('data-theme', t)
  localStorage.setItem('apm-theme', t)
  listeners.forEach(fn => fn())
}

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => { listeners.delete(cb) }
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getTheme)

  const toggle = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }, [theme])

  return { theme, toggle }
}

export function toggleThemeGlobal() {
  setTheme(getTheme() === 'dark' ? 'light' : 'dark')
}
