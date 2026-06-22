import type { BackendInfo, Device, JobRequest, JobStatus } from './types'

/** Typed client for the local FastAPI sidecar. The base URL comes from the main process. */
export class Api {
  constructor(private base: string) {}

  private async json<T>(path: string, init?: RequestInit): Promise<T> {
    const r = await fetch(`${this.base}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init
    })
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
    return r.json() as Promise<T>
  }

  health = () => this.json<{ status: string; version: string }>('/health')
  devices = () => this.json<{ devices: Device[] }>('/devices').then((d) => d.devices)
  backends = () =>
    this.json<{ diarization: BackendInfo[]; transcription: BackendInfo[] }>('/backends')

  getSettings = () => this.json<Record<string, unknown>>('/settings')
  putSettings = (s: Record<string, unknown>) =>
    this.json('/settings', { method: 'PUT', body: JSON.stringify(s) })
  setSecret = (key: string, value: string) =>
    this.json('/secrets', { method: 'POST', body: JSON.stringify({ key, value }) })

  createJob = (req: JobRequest) =>
    this.json<JobStatus>('/jobs', { method: 'POST', body: JSON.stringify(req) })
  getJob = (id: string) => this.json<JobStatus>(`/jobs/${id}`)
  cancelJob = (id: string) => this.json(`/jobs/${id}/cancel`, { method: 'POST' })
  relabel = (id: string, names: Record<string, string>) =>
    this.json<JobStatus>(`/jobs/${id}/relabel`, {
      method: 'POST',
      body: JSON.stringify({ names })
    })

  /** Open the job-progress WebSocket; returns a closer. */
  events(id: string, onEvent: (e: Record<string, unknown>) => void): () => void {
    const wsUrl = this.base.replace(/^http/, 'ws') + `/jobs/${id}/events`
    const ws = new WebSocket(wsUrl)
    ws.onmessage = (m) => onEvent(JSON.parse(m.data))
    return () => ws.close()
  }
}
