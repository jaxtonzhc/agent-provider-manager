import { useState, useCallback } from 'react'

interface ApmResult {
  stdout: string
  stderr: string
  code: number
}

interface ApmHook {
  exec: (args: string[]) => Promise<ApmResult>
  loading: boolean
}

const MOCK: Record<string, ApmResult> = {
  '--json provider list': {
    stdout: JSON.stringify([
      { slug: 'deepseek', name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', anthropic_base_url: 'https://api.deepseek.com/anthropic', api_key: 'sk-1234...5678', models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'], protocol: 'openai-compatible' },
      { slug: 'openrouter', name: 'OpenRouter', base_url: 'https://openrouter.ai/api/v1', anthropic_base_url: 'https://openrouter.ai/api/v1', api_key: 'sk-or-1234...5678', models: ['claude-3.5-sonnet', 'gpt-4o', 'llama-3-70b'], protocol: 'openai-compatible' },
      { slug: 'siliconflow', name: 'SiliconFlow', base_url: 'https://api.siliconflow.cn/v1', api_key: 'sf-1234...5678', models: ['qwen-72b', 'deepseek-v2'], protocol: 'openai-compatible' },
    ]),
    stderr: '', code: 0
  },
  '--json status': {
    stdout: JSON.stringify({
      providers: [
        { slug: 'deepseek', name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1' },
        { slug: 'openrouter', name: 'OpenRouter', base_url: 'https://openrouter.ai/api/v1' },
        { slug: 'siliconflow', name: 'SiliconFlow', base_url: 'https://api.siliconflow.cn/v1' },
      ],
      agents: [
        { agent: 'cursor', installed: true, current: { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', provider_slug: 'deepseek' } },
        { agent: 'codex', installed: true, current: { base_url: 'https://openrouter.ai/api/v1', provider_slug: 'openrouter' } },
        { agent: 'claude-code', installed: true, current: { base_url: 'https://api.deepseek.com/anthropic', model: 'deepseek-chat', provider_slug: 'deepseek' } },
        { agent: 'zcode', installed: true, current: { base_url: 'https://api.siliconflow.cn/v1', provider_slug: 'siliconflow' } },
        { agent: 'copilot', installed: false, current: null },
        { agent: 'opencode', installed: true, current: { base_url: 'https://api.siliconflow.cn/v1', model: 'qwen-72b', provider_slug: 'siliconflow' } },
        { agent: 'hermes', installed: false, current: null },
        { agent: 'pi', installed: true, current: { base_url: 'https://api.deepseek.com/v1', provider_slug: 'deepseek' } },
      ],
    }),
    stderr: '', code: 0
  },
  '--json scan': {
    stdout: JSON.stringify([
      { name: 'cursor', installed: true },
      { name: 'codex', installed: true },
      { name: 'claude-code', installed: true },
      { name: 'zcode', installed: true },
      { name: 'copilot', installed: false },
      { name: 'opencode', installed: true },
      { name: 'hermes', installed: false },
      { name: 'pi', installed: true },
    ]),
    stderr: '', code: 0
  },
  '--json snapshot list': {
    stdout: JSON.stringify([
      { name: 'backup-2024-06-20', created_at: '2024-06-20T14:30:00', agents: ['cursor', 'codex', 'zcode'] },
      { name: 'pre-migration', created_at: '2024-06-18T09:15:00', agents: ['cursor', 'codex', 'claude-code', 'zcode', 'opencode', 'pi'] },
      { name: 'initial-setup', created_at: '2024-06-10T11:00:00', agents: ['cursor', 'codex'] },
    ]),
    stderr: '', code: 0
  },
}

function mockExec(args: string[]): Promise<ApmResult> {
  return new Promise(resolve => {
    setTimeout(() => {
      const full = args.join(' ')
      const key3 = args.slice(0, 3).join(' ')
      const key2 = args.slice(0, 2).join(' ')
      resolve(MOCK[full] || MOCK[key3] || MOCK[key2] || { stdout: `Executed: apm ${full}`, stderr: '', code: 0 })
    }, 200 + Math.random() * 300)
  })
}

export function useApm(): ApmHook {
  const [loading, setLoading] = useState(false)

  const exec = useCallback(async (args: string[]): Promise<ApmResult> => {
    setLoading(true)
    try {
      if (typeof window !== 'undefined' && 'apm' in window) {
        return await (window as any).apm.exec(args)
      }
      return await mockExec(args)
    } finally {
      setLoading(false)
    }
  }, [])

  return { exec, loading }
}
