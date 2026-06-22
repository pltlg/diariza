import { ChildProcess, spawn } from 'child_process'
import { createServer } from 'net'
import { existsSync } from 'fs'
import { join } from 'path'
import { app } from 'electron'

let child: ChildProcess | null = null
let baseUrl = ''

/** Find a free localhost TCP port. */
function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const srv = createServer()
    srv.once('error', reject)
    srv.listen(0, '127.0.0.1', () => {
      const addr = srv.address()
      const port = typeof addr === 'object' && addr ? addr.port : 0
      srv.close(() => resolve(port))
    })
  })
}

/**
 * Resolve how to launch the Python engine:
 *  - dev: `python -m diariza.server` (DIARIZA_PYTHON overrides the interpreter)
 *  - prod: the bundled PyInstaller binary under resources/backend/
 */
function resolveCommand(port: number): { cmd: string; args: string[] } {
  const portArgs = ['--host', '127.0.0.1', '--port', String(port)]
  const bundled = join(
    process.resourcesPath || '',
    'backend',
    process.platform === 'win32' ? 'diariza-backend.exe' : 'diariza-backend'
  )
  if (app.isPackaged && existsSync(bundled)) {
    return { cmd: bundled, args: portArgs }
  }
  const py = process.env.DIARIZA_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
  return { cmd: py, args: ['-m', 'diariza.server', ...portArgs] }
}

async function waitForHealth(url: string, timeoutMs = 60000): Promise<void> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const r = await fetch(`${url}/health`)
      if (r.ok) return
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 400))
  }
  throw new Error('diariza backend did not become healthy in time')
}

export async function startSidecar(onLog?: (line: string) => void): Promise<string> {
  const port = await freePort()
  const { cmd, args } = resolveCommand(port)
  child = spawn(cmd, args, { env: { ...process.env }, windowsHide: true })
  child.stdout?.on('data', (d) => onLog?.(d.toString()))
  child.stderr?.on('data', (d) => onLog?.(d.toString()))
  child.on('exit', (code) => onLog?.(`[backend exited with code ${code}]`))
  baseUrl = `http://127.0.0.1:${port}`
  await waitForHealth(baseUrl)
  return baseUrl
}

export function backendUrl(): string {
  return baseUrl
}

export function stopSidecar(): void {
  if (child && !child.killed) {
    child.kill()
    child = null
  }
}
