import { useEffect, useState } from 'react'
import { useApm } from '../hooks/useApm'

interface StatusInfo {
  providers: number
  agents: { name: string; synced: boolean; provider?: string }[]
  lastSync?: string
}

export default function Dashboard() {
  const { exec } = useApm()
  const [status, setStatus] = useState<StatusInfo | null>(null)

  useEffect(() => {
    (async () => {
      const res = await exec(['--json', 'status'])
      try {
        const data = JSON.parse(res.stdout)
        const agents = (data.agents || []).map((a: any) => ({
          name: a.agent,
          synced: a.installed && !!a.current,
          provider: a.current?.base_url,
        }))
        setStatus({ providers: (data.providers || []).length, agents })
      } catch { /* fallback empty */ }
    })()
  }, [exec])

  const syncedCount = status?.agents.filter(a => a.synced).length ?? 0
  const totalAgents = status?.agents.length ?? 0

  return (
    <div>
      <h2 className="text-[22px] font-semibold tracking-tight mb-8">Overview</h2>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        <StatCard label="Providers" value={status?.providers ?? '—'} description="Configured API sources" />
        <StatCard label="Agents Synced" value={`${syncedCount}/${totalAgents}`} description="With active provider" accent={syncedCount === totalAgents && totalAgents > 0} />
        <StatCard label="Total Agents" value={totalAgents || '—'} description="Detected on this machine" />
      </div>

      {/* Agents Grid */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-[14px] font-semibold">Agent Status</h3>
        <span className="text-[12px] text-text-muted">{syncedCount} of {totalAgents} synced</span>
      </div>
      <div className="grid grid-cols-2 gap-2.5">
        {status?.agents.map(agent => (
          <div key={agent.name} className="flex items-center gap-3 px-4 py-3 bg-surface-1 rounded-lg border border-border hover:border-border-hover transition-colors min-w-0">
            <div className={`w-2 h-2 rounded-full shrink-0 ${agent.synced ? 'bg-success' : 'bg-border'}`} />
            <span className="text-[13px] font-medium text-text-primary shrink-0">{agent.name}</span>
            {agent.provider && agent.provider !== '—' && (
              <span className="text-[11px] text-text-muted font-mono bg-surface-3 px-2 py-0.5 rounded truncate ml-auto max-w-[60%]">{agent.provider}</span>
            )}
          </div>
        ))}
      </div>
      {!status && <LoadingSkeleton />}
    </div>
  )
}

function StatCard({ label, value, description, accent }: { label: string; value: string | number; description: string; accent?: boolean }) {
  return (
    <div className="px-5 py-4 bg-surface-1 rounded-lg border border-border">
      <div className="text-[12px] text-text-secondary mb-1">{label}</div>
      <div className={`text-[24px] font-semibold tracking-tight ${accent ? 'text-success' : 'text-text-primary'}`}>{value}</div>
      <div className="text-[11px] text-text-muted mt-0.5">{description}</div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-2.5 animate-pulse">
      {[1,2,3,4].map(i => <div key={i} className="h-12 bg-surface-2 rounded-lg" />)}
    </div>
  )
}
