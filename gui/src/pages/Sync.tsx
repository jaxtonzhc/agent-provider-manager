import { useEffect, useState, useCallback } from 'react'
import { useApm } from '../hooks/useApm'
import { useToast } from '../components/Toast'

export default function Sync() {
  const { exec } = useApm()
  const { toast } = useToast()
  const [providers, setProviders] = useState<string[]>([])
  const [agents, setAgents] = useState<{ name: string; checked: boolean }[]>([])
  const [selected, setSelected] = useState('')
  const [output, setOutput] = useState('')
  const [syncing, setSyncing] = useState(false)

  const load = useCallback(async () => {
    const [provRes, scanRes] = await Promise.all([
      exec(['--json', 'provider', 'list']),
      exec(['--json', 'scan']),
    ])
    try {
      const provs = JSON.parse(provRes.stdout) as any[]
      const names = provs.map(p => p.slug || p.name)
      setProviders(names)
      if (names[0] && !selected) setSelected(names[0])
    } catch { /* empty */ }
    try {
      const scanned = JSON.parse(scanRes.stdout) as any[]
      const installed = scanned.filter(a => a.installed).map(a => ({ name: a.name, checked: true }))
      setAgents(installed)
    } catch { /* empty */ }
  }, [exec, selected])

  useEffect(() => { load() }, [load])

  function toggleAgent(name: string) {
    setAgents(prev => prev.map(a => a.name === name ? { ...a, checked: !a.checked } : a))
  }
  function toggleAll(checked: boolean) {
    setAgents(prev => prev.map(a => ({ ...a, checked })))
  }

  async function handleSync() {
    const targets = agents.filter(a => a.checked).map(a => a.name)
    if (!selected || targets.length === 0) return
    setSyncing(true)
    setOutput('')
    const res = await exec(['sync', selected, '--agents', targets.join(',')])
    const out = res.stdout + (res.stderr ? `\n${res.stderr}` : '')
    setOutput(out)
    setSyncing(false)
    toast(res.code === 0 ? `Synced ${selected} → ${targets.length} agents` : 'Sync failed', res.code === 0 ? 'success' : 'error')
  }

  const checkedCount = agents.filter(a => a.checked).length

  return (
    <div>
      <h2 className="text-[22px] font-semibold tracking-tight mb-8">Sync</h2>

      {/* Step 1 */}
      <section className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <StepBadge n={1} />
          <span className="text-[13px] font-medium">Select Provider</span>
        </div>
        <select value={selected} onChange={e => setSelected(e.target.value)} className="input-field max-w-[320px]">
          {providers.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </section>

      {/* Step 2 */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <StepBadge n={2} />
            <span className="text-[13px] font-medium">Select Agents</span>
          </div>
          <button onClick={() => toggleAll(checkedCount < agents.length)} className="text-[12px] text-accent hover:underline">
            {checkedCount === agents.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {agents.map(agent => (
            <label key={agent.name} className={`flex items-center gap-2.5 px-3 py-2.5 rounded-md border cursor-pointer transition-colors ${
              agent.checked ? 'border-accent bg-accent-light' : 'border-border bg-surface-1 hover:bg-surface-2'
            }`}>
              <input type="checkbox" checked={agent.checked} onChange={() => toggleAgent(agent.name)}
                className="w-3.5 h-3.5 accent-accent" />
              <span className="text-[13px]">{agent.name}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Step 3 */}
      <section className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <StepBadge n={3} />
          <span className="text-[13px] font-medium">Execute</span>
        </div>
        <button onClick={handleSync} disabled={syncing || !selected || checkedCount === 0}
          className="h-9 px-5 bg-text-primary text-bg text-[13px] font-medium rounded-md hover:opacity-90 disabled:opacity-40 transition-opacity">
          {syncing ? 'Syncing…' : `Sync ${selected} → ${checkedCount} agent${checkedCount !== 1 ? 's' : ''}`}
        </button>
      </section>

      {/* Output */}
      {output && (
        <div className="mt-6 border border-border rounded-lg overflow-hidden">
          <div className="px-4 py-2 bg-surface-2 border-b border-border text-[12px] text-text-secondary font-medium">Output</div>
          <pre className="p-4 bg-surface-1 text-[12px] font-mono text-text-secondary whitespace-pre-wrap max-h-[200px] overflow-y-auto leading-relaxed">
            {output}
          </pre>
        </div>
      )}
    </div>
  )
}

function StepBadge({ n }: { n: number }) {
  return (
    <span className="w-5 h-5 rounded-full bg-accent text-white text-[11px] font-bold flex items-center justify-center">{n}</span>
  )
}
