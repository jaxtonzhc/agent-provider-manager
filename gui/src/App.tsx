import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import { ToastProvider } from './components/Toast'
import { useTheme, toggleThemeGlobal } from './hooks/useTheme'
import Dashboard from './pages/Dashboard'
import Providers from './pages/Providers'
import Agents from './pages/Agents'
import Sync from './pages/Sync'
import Snapshots from './pages/Snapshots'

type Page = 'dashboard' | 'providers' | 'agents' | 'sync' | 'snapshots'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const { theme, toggle } = useTheme()

  useEffect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if (!e.metaKey) return
      const map: Record<string, Page> = { '1': 'dashboard', '2': 'providers', '3': 'agents', '4': 'sync', '5': 'snapshots' }
      if (map[e.key]) { e.preventDefault(); setPage(map[e.key]) }
      if (e.key === 'd') { e.preventDefault(); toggleThemeGlobal() }
    }
    window.addEventListener('keydown', handleKeydown)
    return () => window.removeEventListener('keydown', handleKeydown)
  }, [])

  const pages: Record<Page, React.ReactNode> = {
    dashboard: <Dashboard />,
    providers: <Providers />,
    agents: <Agents />,
    sync: <Sync />,
    snapshots: <Snapshots />,
  }

  return (
    <ToastProvider>
      <div className="flex h-screen bg-bg select-none">
        <div className="fixed top-0 left-0 right-0 h-8 z-40 pointer-events-none" style={{ WebkitAppRegion: 'drag' } as React.CSSProperties} />
        <Sidebar current={page} onNavigate={setPage} />
        <main className="flex-1 overflow-y-auto relative">
          {/* Theme toggle - fixed top right */}
          <button onClick={toggle} className="fixed top-3 right-4 z-50 flex items-center gap-1.5 h-7 px-3 text-[12px] text-text-secondary border border-border rounded-md hover:bg-surface-2 hover:text-text-primary hover:border-border-hover transition-colors bg-surface-1 shadow-sm">
            <span className="text-[14px]">{theme === 'dark' ? '🌙' : '☀️'}</span>
            <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
          </button>
          <div className="max-w-[960px] mx-auto px-8 py-10">
            {pages[page]}
          </div>
        </main>
      </div>
    </ToastProvider>
  )
}
