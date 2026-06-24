import { useEffect, useState, useCallback } from 'react'
import { useApm } from '../hooks/useApm'
import { useToast } from '../components/Toast'

interface Provider { slug: string; name: string; models: string[] }
interface AgentStatus { agent: string; installed: boolean; current: { base_url?: string; model?: string; provider_slug?: string } | null }

export default function Dashboard() {
  const { exec } = useApm()
  const { toast } = useToast()
  const [providers, setProviders] = useState<Provider[]>([])
  const [agents, setAgents] = useState<AgentStatus[]>([])
  const [switching, setSwitching] = useState<string | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)

  const load = useCallback(async () => {
    const res = await exec(['--json', 'status'])
    try {
      const data = JSON.parse(res.stdout)
      setProviders((data.providers || []).map((p: any) => ({
        slug: p.slug, name: p.name || p.slug, models: p.models || [],
      })))
      setAgents(data.agents || [])
    } catch { /* empty */ }
  }, [exec])

  useEffect(() => { load() }, [load])

  const installedAgents = agents.filter(a => a.installed)

  async function handleSwitch(agentName: string, providerSlug: string, model?: string) {
    setSwitching(`${agentName}-${providerSlug}`)
    const args = ['switch', providerSlug, '--agents', agentName]
    if (model) args.push('--model', model)
    const res = await exec(args)
    setSwitching(null)
    if (res.code === 0) {
      toast(`Switched ${agentName} → ${providerSlug}${model ? ` (${model})` : ''}`, 'success')
      load()
    } else {
      toast(res.stderr || 'Switch failed', 'error')
    }
  }

  async function handleSwitchAll(providerSlug: string) {
    setSwitching(`all-${providerSlug}`)
    const targets = installedAgents.map(a => a.agent).join(',')
    const res = await exec(['switch', providerSlug, '--agents', targets])
    setSwitching(null)
    if (res.code === 0) {
      toast(`All agents → ${providerSlug}`, 'success')
      load()
    } else {
      toast(res.stderr || 'Switch failed', 'error')
    }
  }

  return (
    <div>
      <h2 className="text-[22px] font-semibold tracking-tight mb-2">Switch</h2>
      <p className="text-[13px] text-text-secondary mb-8">One-click provider switching for all your agents</p>

      {/* Provider selector row */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[12px] font-medium text-text-secondary uppercase tracking-wide">Active Provider</span>
        </div>
        <div className="flex gap-2 flex-wrap">
          {providers.map(p => {
            const isActive = installedAgents.length > 0 && installedAgents.every(a => a.current?.provider_slug === p.slug)
            const isPartial = installedAgents.some(a => a.current?.provider_slug === p.slug)
            return (
              <button
                key={p.slug}
                onClick={() => setSelectedProvider(selectedProvider === p.slug ? null : p.slug)}
                className={`relative px-4 py-2.5 rounded-lg border text-[13px] font-medium transition-all ${
                  isActive
                    ? 'border-success bg-success/10 text-success shadow-sm'
                    : isPartial
                      ? 'border-accent bg-accent-light text-accent'
                      : selectedProvider === p.slug
                        ? 'border-accent bg-accent-light text-accent'
                        : 'border-border bg-surface-1 text-text-primary hover:border-border-hover hover:bg-surface-2'
                }`}
              >
                <span>{p.slug}</span>
                {isActive && <span className="ml-2 text-[10px] opacity-70">✓ All</span>}
                {isPartial && !isActive && <span className="ml-2 text-[10px] opacity-70">partial</span>}
              </button>
            )
          })}
        </div>
      </div>

      {/* Switch All button */}
      {selectedProvider && (
        <div className="mb-6 p-4 bg-surface-2 rounded-lg border border-border">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[13px] font-medium">Switch all agents to </span>
              <span className="text-[13px] font-bold text-accent">{selectedProvider}</span>
            </div>
            <button
              onClick={() => handleSwitchAll(selectedProvider)}
              disabled={!!switching}
              className="h-8 px-4 bg-accent text-white text-[13px] font-medium rounded-md hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {switching === `all-${selectedProvider}` ? 'Switching…' : 'Switch All →'}
            </button>
          </div>
        </div>
      )}

      {/* Agent → Provider mapping grid */}
      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Agent</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Current Provider</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Model</th>
              <th className="text-right px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Quick Switch</th>
            </tr>
          </thead>
          <tbody>
            {installedAgents.map(agent => (
              <tr key={agent.agent} className="border-b border-border hover:bg-surface-2 transition-colors group">
                <td className="px-4 py-3">
                  <span className="font-medium text-text-primary">{agent.agent}</span>
                </td>
                <td className="px-4 py-3">
                  {agent.current?.provider_slug ? (
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-success" />
                      <span className="text-text-primary">{agent.current.provider_slug}</span>
                    </span>
                  ) : (
                    <span className="text-text-muted">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-text-secondary font-mono text-[12px]">{agent.current?.model || '—'}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex gap-1 justify-end">
                    {providers.filter(p => p.slug !== agent.current?.provider_slug).map(p => (
                      <button
                        key={p.slug}
                        onClick={() => handleSwitch(agent.agent, p.slug)}
                        disabled={!!switching}
                        className="px-2.5 py-1 text-[11px] font-medium rounded border border-border text-text-secondary hover:border-accent hover:text-accent hover:bg-accent-light transition-all disabled:opacity-40"
                      >
                        {switching === `${agent.agent}-${p.slug}` ? '…' : p.slug}
                      </button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {installedAgents.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-12 text-center text-text-muted">No agents detected</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Stats footer */}
      <div className="mt-6 flex gap-4">
        <MiniStat label="Providers" value={providers.length} />
        <MiniStat label="Agents" value={installedAgents.length} />
        <MiniStat label="Synced" value={installedAgents.filter(a => a.current).length} accent />
      </div>
    </div>
  )
}

function MiniStat({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-surface-1 rounded-md border border-border">
      <span className={`text-[16px] font-semibold ${accent ? 'text-success' : 'text-text-primary'}`}>{value}</span>
      <span className="text-[11px] text-text-muted">{label}</span>
    </div>
  )
}
