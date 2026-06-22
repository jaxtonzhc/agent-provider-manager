import { useEffect, useState, useCallback } from 'react'
import { useApm } from '../hooks/useApm'
import { useToast } from '../components/Toast'

interface Agent {
  name: string
  installed: boolean
  provider?: string
}

interface AgentConfig {
  provider?: string
  openai_url?: string
  anthropic_url?: string
  api_key?: string
  models?: string[]
  last_synced?: string
  config_path?: string
}

export default function Agents() {
  const { exec } = useApm()
  const { toast } = useToast()
  const [agents, setAgents] = useState<Agent[]>([])
  const [syncing, setSyncing] = useState<string | null>(null)
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [agentConfig, setAgentConfig] = useState<AgentConfig | null>(null)
  const [loadingConfig, setLoadingConfig] = useState(false)

  const loadAgents = useCallback(async () => {
    const res = await exec(['--json', 'status'])
    try {
      const data = JSON.parse(res.stdout)
      setAgents((data.agents || []).map((a: any) => ({
        name: a.agent,
        installed: a.installed,
        provider: a.current?.base_url,
      })))
    } catch { setAgents([]) }
  }, [exec])

  useEffect(() => { loadAgents() }, [loadAgents])

  async function handleSync(agentName: string) {
    setSyncing(agentName)
    const res = await exec(['sync', '--agents', agentName])
    setSyncing(null)
    toast(res.code === 0 ? `${agentName} synced` : `Sync failed for ${agentName}`, res.code === 0 ? 'success' : 'error')
    loadAgents()
  }

  async function toggleConfig(agentName: string) {
    if (expandedAgent === agentName) {
      setExpandedAgent(null)
      setAgentConfig(null)
      return
    }
    setExpandedAgent(agentName)
    setLoadingConfig(true)
    const res = await exec(['--json', 'status'])
    try {
      const data = JSON.parse(res.stdout)
      const agent = (data.agents || []).find((a: any) => a.agent === agentName)
      const cur = agent?.current
      setAgentConfig(cur ? {
        provider: cur.provider_slug,
        openai_url: cur.base_url,
        anthropic_url: cur.anthropic_base_url,
        api_key: cur.api_key ? cur.api_key.slice(0, 4) + '****' + cur.api_key.slice(-4) : undefined,
        models: cur.model ? [cur.model] : cur.models,
        config_path: cur.config_path,
      } : null)
    } catch { setAgentConfig(null) }
    setLoadingConfig(false)
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-[22px] font-semibold tracking-tight">Agents</h2>
        <p className="text-[13px] text-text-secondary mt-1">AI coding agents detected on this machine</p>
      </div>

      <div className="space-y-2">
        {agents.map(agent => (
          <div key={agent.name} className="bg-surface-1 rounded-lg border border-border overflow-hidden">
            {/* Agent Row */}
            <div className="flex items-center justify-between px-5 py-3.5 hover:bg-surface-2 transition-colors group">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-md flex items-center justify-center text-[12px] font-bold ${
                  agent.installed ? 'bg-accent-light text-accent' : 'bg-surface-3 text-text-muted'
                }`}>
                  {agent.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium text-text-primary">{agent.name}</span>
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                      agent.installed ? 'bg-success/10 text-success' : 'bg-surface-3 text-text-muted'
                    }`}>
                      {agent.installed ? 'Installed' : 'Not Found'}
                    </span>
                  </div>
                  {agent.provider && (
                    <span className="text-[11px] text-text-muted mt-0.5 block">Provider: {agent.provider}</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {agent.installed && (
                  <>
                    <button onClick={() => toggleConfig(agent.name)}
                      className={`h-7 px-2.5 text-[12px] border rounded-md transition-colors ${
                        expandedAgent === agent.name
                          ? 'border-accent text-accent bg-accent-light'
                          : 'border-border text-text-secondary hover:bg-surface-3 hover:text-text-primary'
                      }`}>
                      {expandedAgent === agent.name ? 'Hide Config' : 'Config'}
                    </button>
                    <button onClick={() => handleSync(agent.name)} disabled={syncing === agent.name}
                      className="h-7 px-2.5 text-[12px] text-accent border border-accent/30 rounded-md hover:bg-accent-light disabled:opacity-50 transition-colors">
                      {syncing === agent.name ? 'Syncing…' : 'Sync'}
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Config Panel */}
            {expandedAgent === agent.name && (
              <div className="px-5 py-4 border-t border-border bg-surface-2">
                {loadingConfig ? (
                  <div className="text-[12px] text-text-muted animate-pulse">Loading config…</div>
                ) : agentConfig ? (
                  <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-[12px]">
                    <ConfigField label="Provider" value={agentConfig.provider} />
                    <ConfigField label="Last Synced" value={agentConfig.last_synced} />
                    <ConfigField label="OpenAI Endpoint" value={agentConfig.openai_url} mono />
                    <ConfigField label="Anthropic Endpoint" value={agentConfig.anthropic_url} mono />
                    <ConfigField label="API Key" value={agentConfig.api_key} mono />
                    <ConfigField label="Config Path" value={agentConfig.config_path} mono />
                    {agentConfig.models && agentConfig.models.length > 0 && (
                      <div className="col-span-2">
                        <span className="text-text-muted block mb-1">Models</span>
                        <div className="flex flex-wrap gap-1.5">
                          {agentConfig.models.map(m => (
                            <span key={m} className="px-2 py-0.5 bg-surface-3 rounded text-[11px] text-text-secondary font-mono">{m}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-[12px] text-text-muted">No configuration found</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {agents.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-text-muted">Scanning for agents…</p>
        </div>
      )}
    </div>
  )
}

function ConfigField({ label, value, mono }: { label: string; value?: string | null; mono?: boolean }) {
  if (!value) return (
    <div>
      <span className="text-text-muted block mb-0.5">{label}</span>
      <span className="text-text-muted">—</span>
    </div>
  )
  return (
    <div>
      <span className="text-text-muted block mb-0.5">{label}</span>
      <span className={`text-text-primary ${mono ? 'font-mono text-[11px]' : ''}`}>{value}</span>
    </div>
  )
}
