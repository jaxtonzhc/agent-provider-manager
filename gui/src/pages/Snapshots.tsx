import { useEffect, useState, useCallback } from 'react'
import { useApm } from '../hooks/useApm'
import { useToast } from '../components/Toast'

interface Snapshot {
  name: string
  created: string
  agents: string
}

export default function Snapshots() {
  const { exec } = useApm()
  const { toast } = useToast()
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [confirmAction, setConfirmAction] = useState<{ type: 'restore' | 'delete'; name: string } | null>(null)

  const loadSnapshots = useCallback(async () => {
    const res = await exec(['--json', 'snapshot', 'list'])
    try {
      const data = JSON.parse(res.stdout) as any[]
      setSnapshots(data.map(s => ({
        name: s.name,
        created: s.created_at || '',
        agents: Array.isArray(s.agents) ? s.agents.join(', ') : (s.agents || ''),
      })))
    } catch { setSnapshots([]) }
  }, [exec])

  useEffect(() => { loadSnapshots() }, [loadSnapshots])

  async function handleAction() {
    if (!confirmAction) return
    const { type, name } = confirmAction
    const res = await exec(['snapshot', type, name])
    toast(res.code === 0 ? `${type === 'restore' ? 'Restored' : 'Deleted'} ${name}` : 'Operation failed', res.code === 0 ? 'success' : 'error')
    setConfirmAction(null)
    loadSnapshots()
  }

  async function handleSave() {
    const res = await exec(['snapshot', 'save'])
    toast(res.code === 0 ? 'Snapshot saved' : 'Save failed', res.code === 0 ? 'success' : 'error')
    loadSnapshots()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-[22px] font-semibold tracking-tight">Snapshots</h2>
          <p className="text-[13px] text-text-secondary mt-1">Save and restore provider configurations</p>
        </div>
        <button onClick={handleSave} className="h-8 px-3.5 bg-accent text-white text-[13px] font-medium rounded-md hover:opacity-90 transition-opacity">
          Save Snapshot
        </button>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Name</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Created</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Agents</th>
              <th className="text-right px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody>
            {snapshots.map(snap => (
              <tr key={snap.name} className="border-b border-border hover:bg-surface-2 transition-colors group">
                <td className="px-4 py-3 font-mono text-[12px] font-medium">{snap.name}</td>
                <td className="px-4 py-3 text-text-secondary">{snap.created}</td>
                <td className="px-4 py-3 text-text-secondary">{snap.agents}</td>
                <td className="px-4 py-3 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => setConfirmAction({ type: 'restore', name: snap.name })}
                    className="px-2 py-1 text-[12px] text-accent hover:bg-accent-light rounded transition-colors">Restore</button>
                  <button onClick={() => setConfirmAction({ type: 'delete', name: snap.name })}
                    className="px-2 py-1 text-[12px] text-error hover:bg-error-light rounded transition-colors ml-1">Delete</button>
                </td>
              </tr>
            ))}
            {snapshots.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-16 text-center">
                <p className="text-text-muted mb-2">No snapshots yet</p>
                <p className="text-[12px] text-text-muted">Snapshots let you save and restore the full state of all provider configs</p>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Confirm Dialog */}
      {confirmAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setConfirmAction(null)} />
          <div className="relative bg-surface-1 border border-border rounded-xl p-6 w-[400px] shadow-2xl">
            <h3 className="text-[16px] font-semibold mb-2 capitalize">{confirmAction.type} Snapshot?</h3>
            <p className="text-[13px] text-text-secondary mb-6">
              {confirmAction.type === 'restore'
                ? `This will restore the configuration from "${confirmAction.name}" to all agents.`
                : `This will permanently delete the snapshot "${confirmAction.name}".`}
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmAction(null)} className="h-8 px-4 text-[13px] text-text-secondary hover:text-text-primary transition-colors">Cancel</button>
              <button onClick={handleAction}
                className={`h-8 px-4 text-[13px] font-medium rounded-md transition-opacity hover:opacity-90 ${
                  confirmAction.type === 'delete' ? 'bg-error text-white' : 'bg-accent text-white'
                }`}>
                {confirmAction.type === 'restore' ? 'Restore' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
