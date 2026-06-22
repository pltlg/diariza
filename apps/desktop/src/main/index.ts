import { app, BrowserWindow, dialog, ipcMain, shell } from 'electron'
import { join } from 'path'
import { backendUrl, startSidecar, stopSidecar } from './sidecar'

let win: BrowserWindow | null = null
const logBuffer: string[] = []

function createWindow(): void {
  win = new BrowserWindow({
    width: 1100,
    height: 800,
    show: false,
    title: 'diariza',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true
    }
  })

  win.on('ready-to-show', () => win?.show())

  const devUrl = process.env['ELECTRON_RENDERER_URL']
  if (devUrl) {
    win.loadURL(devUrl)
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// --- IPC: backend URL, file/dir pickers, log tail ---
ipcMain.handle('backend:url', () => backendUrl())
ipcMain.handle('backend:logs', () => logBuffer.slice(-300))

ipcMain.handle('dialog:openFile', async (_e, filters?: Electron.FileFilter[]) => {
  const r = await dialog.showOpenDialog(win!, {
    properties: ['openFile'],
    filters: filters ?? [{ name: 'Media & transcripts', extensions: ['mp4', 'mkv', 'mov', 'wav', 'mp3', 'm4a', 'vtt', 'srt'] }]
  })
  return r.canceled ? null : r.filePaths[0]
})

ipcMain.handle('dialog:openDir', async () => {
  const r = await dialog.showOpenDialog(win!, { properties: ['openDirectory', 'createDirectory'] })
  return r.canceled ? null : r.filePaths[0]
})

ipcMain.handle('shell:showItem', (_e, p: string) => shell.showItemInFolder(p))

app.whenReady().then(async () => {
  createWindow()
  try {
    await startSidecar((line) => {
      logBuffer.push(line)
      win?.webContents.send('backend:log', line)
    })
    win?.webContents.send('backend:ready', backendUrl())
  } catch (e) {
    win?.webContents.send('backend:error', String(e))
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopSidecar()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => stopSidecar())
