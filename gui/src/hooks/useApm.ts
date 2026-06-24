import { useState, useCallback } from 'react'
import { invoke } from '@tauri-apps/api/core'

interface ApmResult {
  stdout: string
  stderr: string
  code: number
}

interface ApmHook {
  exec: (args: string[]) => Promise<ApmResult>
  loading: boolean
}

async function tauriExec(args: string[]): Promise<ApmResult> {
  try {
    return await invoke<ApmResult>('exec_apm', { args })
  } catch (e) {
    return { stdout: '', stderr: String(e), code: 1 }
  }
}

export function useApm(): ApmHook {
  const [loading, setLoading] = useState(false)

  const exec = useCallback(async (args: string[]): Promise<ApmResult> => {
    setLoading(true)
    try {
      return await tauriExec(args)
    } finally {
      setLoading(false)
    }
  }, [])

  return { exec, loading }
}
