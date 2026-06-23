import { useState, useEffect, useCallback } from 'react'
import { useApm } from '../hooks/useApm'

interface RulesStatus {
  source: string | null
  sourceExists: boolean
  agents: Array<{
    agent: string
    status: 'linked' | 'no-ref' | 'missing'
    path: string
  }>
}

export default function Rules() {
  const { exec } = useApm()
  const [status, setStatus] = useState<RulesStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    try {
      const res = await exec(['--json', 'rules', 'status'])
      if (res.code === 0 && res.stdout.trim()) {
        setStatus(JSON.parse(res.stdout))
      } else {
        setStatus(null)
      }
    } catch {
      setStatus(null)
    }
    setLoading(false)
  }, [exec])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const handleSync = async () => {
    setSyncing(true)
    setSyncResult(null)
    try {
      const res = await exec(['rules', 'sync'])
      setSyncResult(res.code === 0 ? 'success' : `Error: ${res.stderr || res.stdout}`)
      await fetchStatus()
    } catch (e) {
      setSyncResult(`Error: ${e}`)
    }
    setSyncing(false)
  }

  const handleOpenFile = async () => {
    if (status?.source) {
      await exec(['--open-file', status.source])
    }
  }

  const statusIcon = (s: string) => {
    if (s === 'linked') return <span className="text-green-500">✓</span>
    if (s === 'no-ref') return <span className="text-yellow-500">!</span>
    return <span className="text-red-500">✗</span>
  }

  const statusLabel = (s: string) => {
    if (s === 'linked') return 'Synced'
    if (s === 'no-ref') return 'Not synced'
    return 'Not found'
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-text-primary">Global Rules</h2>
        <p className="text-sm text-text-secondary mt-1">
          Manage shared rules that apply across all AI agents.
        </p>
      </div>

      {/* Source File Card */}
      <div className="bg-surface-1 border border-border rounded-lg p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-text-primary">Source File</h3>
            {status?.source ? (
              <p className="text-xs text-text-secondary mt-1 font-mono">
                {status.source}
                {status.sourceExists
                  ? <span className="ml-2 text-green-500">exists</span>
                  : <span className="ml-2 text-red-500">not found</span>
                }
              </p>
            ) : (
              <p className="text-xs text-text-muted mt-1">
                Not configured. Run <code className="bg-surface-3 px-1 rounded">apm rules sync</code> to set up.
              </p>
            )}
          </div>
          {status?.source && (
            <button
              onClick={handleOpenFile}
              className="flex items-center gap-1.5 h-8 px-3 text-xs font-medium text-text-primary bg-surface-2 border border-border rounded-md hover:bg-surface-3 transition-colors"
            >
              <IconEdit />
              Open in Editor
            </button>
          )}
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-surface-1 border border-border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="text-sm font-medium text-text-primary">Agent Sync Status</h3>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1.5 h-7 px-3 text-xs font-medium text-white bg-accent rounded-md hover:bg-accent-hover disabled:opacity-50 transition-colors"
          >
            {syncing ? <IconSpinner /> : <IconSync />}
            {syncing ? 'Syncing...' : 'Sync Rules'}
          </button>
        </div>

        {loading ? (
          <div className="px-5 py-8 text-center text-text-muted text-sm">Loading...</div>
        ) : status?.agents?.length ? (
          <div className="divide-y divide-border">
            {status.agents.map(a => (
              <div key={a.agent} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  {statusIcon(a.status)}
                  <span className="text-sm text-text-primary font-medium">{a.agent}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    a.status === 'linked'
                      ? 'bg-green-500/10 text-green-500'
                      : a.status === 'no-ref'
                        ? 'bg-yellow-500/10 text-yellow-500'
                        : 'bg-red-500/10 text-red-500'
                  }`}>
                    {statusLabel(a.status)}
                  </span>
                  <span className="text-[11px] text-text-muted font-mono">{a.path}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-5 py-8 text-center text-text-muted text-sm">
            No agent configuration found.
          </div>
        )}
      </div>

      {/* Sync Result */}
      {syncResult && (
        <div className={`text-xs px-4 py-2 rounded-md ${
          syncResult === 'success'
            ? 'bg-green-500/10 text-green-500'
            : 'bg-red-500/10 text-red-400'
        }`}>
          {syncResult === 'success' ? '✓ Rules synced to all agents.' : syncResult}
        </div>
      )}
    </div>
  )
}

function IconEdit() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M11 2l3 3-9 9H2v-3L11 2z" />
    </svg>
  )
}

function IconSync() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 8a6 6 0 0 1 10.5-4" /><path d="M14 8a6 6 0 0 1-10.5 4" />
      <path d="M12.5 1v3h-3" /><path d="M3.5 15v-3h3" />
    </svg>
  )
}

function IconSpinner() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="animate-spin">
      <path d="M8 1v3M8 12v3M1 8h3M12 8h3" />
    </svg>
  )
}
