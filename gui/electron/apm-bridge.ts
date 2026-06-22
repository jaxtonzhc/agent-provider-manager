import { execFile, execSync } from 'child_process'
import { existsSync } from 'fs'
import { promisify } from 'util'

const execFileAsync = promisify(execFile)

export interface ApmResult {
  stdout: string
  stderr: string
  code: number
}

function resolveApmPath(): string {
  const candidates = [
    process.env.APM_PATH,
    '/usr/local/bin/apm',
    `${process.env.HOME}/bin/apm`,
    `${process.env.HOME}/.local/bin/apm`,
  ]
  for (const p of candidates) {
    if (p && existsSync(p)) return p
  }
  try {
    const shell = process.env.SHELL || '/bin/zsh'
    return execSync(`${shell} -ilc "which apm"`, { encoding: 'utf-8' }).trim()
  } catch {
    return 'apm'
  }
}

const apmBin = resolveApmPath()

function getShellEnv(): Record<string, string> {
  const env = { ...process.env, APM_NO_COLOR: '1' } as Record<string, string>
  if (!env.PATH?.includes('/usr/local/bin')) {
    try {
      const shell = process.env.SHELL || '/bin/zsh'
      const path = execSync(`${shell} -ilc "echo \\$PATH"`, { encoding: 'utf-8' }).trim()
      if (path) env.PATH = path
    } catch { /* keep current PATH */ }
  }
  return env
}

const shellEnv = getShellEnv()

export async function execApm(args: string[]): Promise<ApmResult> {
  try {
    const { stdout, stderr } = await execFileAsync(apmBin, args, {
      encoding: 'utf-8',
      timeout: 30000,
      env: shellEnv,
    })
    return { stdout, stderr, code: 0 }
  } catch (err: unknown) {
    const e = err as { stdout?: string; stderr?: string; code?: number }
    return { stdout: e.stdout ?? '', stderr: e.stderr ?? '', code: e.code ?? 1 }
  }
}
