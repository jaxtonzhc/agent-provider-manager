const navItems = [
  { id: 'dashboard', label: 'Overview', icon: <IconGrid /> },
  { id: 'providers', label: 'Providers', icon: <IconServer /> },
  { id: 'agents', label: 'Agents', icon: <IconBot /> },
  { id: 'sync', label: 'Sync', icon: <IconSync /> },
  { id: 'snapshots', label: 'Snapshots', icon: <IconArchive /> },
] as const

type Page = typeof navItems[number]['id']

export default function Sidebar({ current, onNavigate }: { current: Page; onNavigate: (p: Page) => void }) {
  return (
    <aside className="w-[220px] bg-surface-1 border-r border-border flex flex-col pt-12">
      <div className="px-5 mb-6">
        <div className="flex items-center gap-2.5">
          <img src="./icon-512.png" alt="APM" className="w-7 h-7 rounded-md" />
          <div>
            <h1 className="text-[13px] font-semibold text-text-primary leading-none">APM</h1>
            <p className="text-[11px] text-text-muted mt-0.5">Provider Manager</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] mb-0.5 transition-colors ${
              current === item.id
                ? 'bg-accent-light text-accent font-medium'
                : 'text-text-secondary hover:bg-surface-3 hover:text-text-primary'
            }`}
          >
            <span className="w-4 h-4 flex items-center justify-center opacity-70">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="px-4 py-3 border-t border-border text-[11px] text-text-muted">
        v0.1.2
      </div>
    </aside>
  )
}

function IconGrid() {
  return <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/></svg>
}
function IconServer() {
  return <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="12" height="4" rx="1"/><rect x="2" y="10" width="12" height="4" rx="1"/><circle cx="5" cy="4" r="0.5" fill="currentColor"/><circle cx="5" cy="12" r="0.5" fill="currentColor"/></svg>
}
function IconBot() {
  return <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="4" width="10" height="9" rx="2"/><line x1="8" y1="4" x2="8" y2="2"/><circle cx="8" cy="1.5" r="0.8"/><circle cx="6" cy="8" r="1" fill="currentColor"/><circle cx="10" cy="8" r="1" fill="currentColor"/></svg>
}
function IconSync() {
  return <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 8a6 6 0 0 1 10.5-4"/><path d="M14 8a6 6 0 0 1-10.5 4"/><path d="M12.5 1v3h-3"/><path d="M3.5 15v-3h3"/></svg>
}
function IconArchive() {
  return <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="12" height="3" rx="1"/><path d="M3 5v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5"/><line x1="6" y1="8" x2="10" y2="8"/></svg>
}
