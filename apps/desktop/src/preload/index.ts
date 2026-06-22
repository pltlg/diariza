import { contextBridge, ipcRenderer } from 'electron'

/** Safe, minimal surface exposed to the renderer as `window.diariza`. */
const api = {
  backendUrl: (): Promise<string> => ipcRenderer.invoke('backend:url'),
  getLogs: (): Promise<string[]> => ipcRenderer.invoke('backend:logs'),
  openFile: (filters?: Electron.FileFilter[]): Promise<string | null> =>
    ipcRenderer.invoke('dialog:openFile', filters),
  openDir: (): Promise<string | null> => ipcRenderer.invoke('dialog:openDir'),
  showInFolder: (path: string): Promise<void> => ipcRenderer.invoke('shell:showItem', path),
  onBackendReady: (cb: (url: string) => void) =>
    ipcRenderer.on('backend:ready', (_e, url) => cb(url)),
  onBackendError: (cb: (err: string) => void) =>
    ipcRenderer.on('backend:error', (_e, err) => cb(err)),
  onLog: (cb: (line: string) => void) => ipcRenderer.on('backend:log', (_e, line) => cb(line))
}

contextBridge.exposeInMainWorld('diariza', api)

export type DiarizaApi = typeof api
