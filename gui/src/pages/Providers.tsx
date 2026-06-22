import { useEffect, useState, useCallback } from 'react'
import { useApm } from '../hooks/useApm'
import { useToast } from '../components/Toast'

interface Provider {
  name: string
  baseUrl: string
  anthropicUrl: string
  models: string[]
  apiKey?: string
}

export default function Providers() {
  const { exec } = useApm()
  const { toast } = useToast()
  const [providers, setProviders] = useState<Provider[]>([])
  const [testing, setTesting] = useState<string | null>(null)
  const [editing, setEditing] = useState<Provider | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, 'ok' | 'fail'>>({})

  const loadProviders = useCallback(async () => {
    const res = await exec(['--json', 'provider', 'list'])
    try {
      const data = JSON.parse(res.stdout) as any[]
      setProviders(data.map(p => ({
        name: p.slug || p.name,
        baseUrl: p.base_url || '',
        anthropicUrl: p.anthropic_base_url || '',
        models: p.models || [],
        apiKey: p.api_key,
      })))
    } catch { setProviders([]) }
  }, [exec])

  useEffect(() => { loadProviders() }, [loadProviders])

  async function handleTest(name: string) {
    setTesting(name)
    const res = await exec(['provider', 'test', name])
    const ok = res.code === 0
    setTestResults(prev => ({ ...prev, [name]: ok ? 'ok' : 'fail' }))
    setTesting(null)
    toast(ok ? `${name}: Connected` : `${name}: Failed`, ok ? 'success' : 'error')
  }

  async function handleDelete(name: string) {
    const res = await exec(['provider', 'remove', name])
    if (res.code === 0) {
      toast(`Removed ${name}`, 'info')
      loadProviders()
    } else {
      toast(res.stderr || 'Remove failed', 'error')
    }
    setConfirmDelete(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-[22px] font-semibold tracking-tight">Providers</h2>
          <p className="text-[13px] text-text-secondary mt-1">Manage your API provider configurations</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="h-8 px-3.5 bg-text-primary text-bg text-[13px] font-medium rounded-md hover:opacity-90 transition-opacity">
          Add Provider
        </button>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-border bg-surface-2">
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Name</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Protocols</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Models</th>
              <th className="text-left px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Status</th>
              <th className="text-right px-4 py-3 font-medium text-text-secondary text-[12px] uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.map(p => (
              <tr key={p.name} className="border-b border-border hover:bg-surface-2 transition-colors group">
                <td className="px-4 py-3">
                  <span className="font-medium text-text-primary">{p.name}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    {p.baseUrl && <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-accent-light text-accent">OpenAI</span>}
                    {p.anthropicUrl && <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[#d97706]/10 text-warning">Anthropic</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-text-secondary">{p.models.length}</td>
                <td className="px-4 py-3">
                  {testResults[p.name] === 'ok' && <StatusDot color="success" label="Connected" />}
                  {testResults[p.name] === 'fail' && <StatusDot color="error" label="Failed" />}
                  {!testResults[p.name] && <StatusDot color="muted" label="Unknown" />}
                </td>
                <td className="px-4 py-3 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                  <ActionBtn onClick={() => setEditing(p)}>Edit</ActionBtn>
                  <ActionBtn onClick={() => handleTest(p.name)} disabled={testing === p.name}>
                    {testing === p.name ? '…' : 'Test'}
                  </ActionBtn>
                  <ActionBtn danger onClick={() => setConfirmDelete(p.name)}>Delete</ActionBtn>
                </td>
              </tr>
            ))}
            {providers.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-16 text-center">
                <p className="text-text-muted text-[14px] mb-2">No providers configured</p>
                <button onClick={() => setShowAdd(true)} className="text-accent text-[13px] hover:underline">Add your first provider →</button>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Dialog */}
      {(showAdd || editing) && (
        <ProviderDialog
          provider={editing}
          onClose={() => { setShowAdd(false); setEditing(null) }}
          onSaved={() => { loadProviders(); setShowAdd(false); setEditing(null) }}
        />
      )}

      {/* Delete Confirmation */}
      {confirmDelete && (
        <ConfirmDialog
          title={`Delete "${confirmDelete}"?`}
          description="This will remove the provider configuration. Any agents synced from this provider will keep their current config."
          confirmLabel="Delete"
          danger
          onConfirm={() => handleDelete(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  )
}

function StatusDot({ color, label }: { color: 'success' | 'error' | 'muted'; label: string }) {
  const colors = { success: 'bg-success', error: 'bg-error', muted: 'bg-text-muted' }
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-1.5 h-1.5 rounded-full ${colors[color]}`} />
      <span className="text-[12px] text-text-secondary">{label}</span>
    </span>
  )
}

function ActionBtn({ children, onClick, danger, disabled }: { children: React.ReactNode; onClick?: () => void; danger?: boolean; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-2 py-1 text-[12px] rounded transition-colors disabled:opacity-50 ${
        danger ? 'text-error hover:bg-error-light' : 'text-text-secondary hover:text-text-primary hover:bg-surface-3'
      }`}
    >
      {children}
    </button>
  )
}

function ProviderDialog({ provider, onClose, onSaved }: { provider: Provider | null; onClose: () => void; onSaved: () => void }) {
  const { exec } = useApm()
  const { toast } = useToast()
  const isEdit = !!provider
  const [name, setName] = useState(provider?.name ?? '')
  const [baseUrl, setBaseUrl] = useState(provider?.baseUrl ?? '')
  const [anthropicUrl, setAnthropicUrl] = useState(provider?.anthropicUrl ?? '')
  const [apiKey, setApiKey] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!name) return
    if (!baseUrl && !anthropicUrl) { toast('At least one endpoint URL is required', 'error'); return }
    setSaving(true)
    const args = isEdit
      ? ['provider', 'update', provider!.name]
      : ['provider', 'add', name]
    if (isEdit && name !== provider!.name) args.push('--rename', name)
    if (baseUrl) args.push('--url', baseUrl)
    if (anthropicUrl) args.push('--anthropic-url', anthropicUrl)
    if (apiKey) args.push('--key', apiKey)

    const res = await exec(args)
    setSaving(false)
    if (res.code === 0) {
      toast(isEdit ? `Updated ${name}` : `Added ${name}`, 'success')
      onSaved()
    } else {
      toast(res.stderr || 'Operation failed', 'error')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-surface-1 border border-border rounded-xl p-6 w-[520px] shadow-2xl">
        <h3 className="text-[16px] font-semibold mb-6">{isEdit ? `Edit Provider` : 'Add Provider'}</h3>

        <div className="space-y-4">
          <Field label="Name">
            <input value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g. deepseek"
              className="input-field" />
          </Field>

          <div className="pt-2 pb-1">
            <p className="text-[12px] text-text-muted">Fill in the endpoint(s) this provider supports. Leave blank if not applicable.</p>
          </div>

          <Field label="OpenAI-Compatible Endpoint">
            <input value={baseUrl} onChange={e => setBaseUrl(e.target.value)}
              placeholder="https://api.deepseek.com/v1"
              className="input-field font-mono text-[12px]" />
          </Field>
          <Field label="Anthropic-Compatible Endpoint">
            <input value={anthropicUrl} onChange={e => setAnthropicUrl(e.target.value)}
              placeholder="https://api.anthropic.com/v1 (optional)"
              className="input-field font-mono text-[12px]" />
          </Field>

          <Field label="API Key">
            <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
              placeholder={isEdit ? '(leave blank to keep unchanged)' : 'sk-...'}
              className="input-field font-mono text-[12px]" />
          </Field>
        </div>

        <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-border">
          <button onClick={onClose} className="h-8 px-4 text-[13px] text-text-secondary hover:text-text-primary transition-colors">Cancel</button>
          <button onClick={handleSave} disabled={!name || saving}
            className="h-8 px-4 bg-text-primary text-bg text-[13px] font-medium rounded-md hover:opacity-90 disabled:opacity-50 transition-opacity">
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Provider'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ConfirmDialog({ title, description, confirmLabel, danger, onConfirm, onCancel }: {
  title: string; description: string; confirmLabel: string; danger?: boolean; onConfirm: () => void; onCancel: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative bg-surface-1 border border-border rounded-xl p-6 w-[400px] shadow-2xl">
        <h3 className="text-[16px] font-semibold mb-2">{title}</h3>
        <p className="text-[13px] text-text-secondary mb-6">{description}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="h-8 px-4 text-[13px] text-text-secondary hover:text-text-primary transition-colors">Cancel</button>
          <button onClick={onConfirm}
            className={`h-8 px-4 text-[13px] font-medium rounded-md transition-opacity hover:opacity-90 ${
              danger ? 'bg-error text-white' : 'bg-text-primary text-bg'
            }`}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children, disabled }: { label: string; children: React.ReactNode; disabled?: boolean }) {
  return (
    <div className={disabled ? 'opacity-60' : ''}>
      <label className="block text-[12px] font-medium text-text-secondary mb-1.5">{label}</label>
      {children}
    </div>
  )
}
