import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { join } from 'path'
import { exec } from 'child_process'
import { execApm } from './apm-bridge'

let win: BrowserWindow | null = null

const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev')

function createWindow() {
  win = new BrowserWindow({
    width: 960,
    height: 640,
    minWidth: 800,
    minHeight: 500,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 12, y: 12 },
    backgroundColor: '#0a0a0a',
    show: false,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  win.once('ready-to-show', () => win?.show())

  if (isDev) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })

ipcMain.handle('apm:exec', async (_event, args: string[]) => {
  // Intercept --open-file command to open in editor
  if (args[0] === '--open-file' && args[1]) {
    const filePath = args[1]
    // Try code (VSCode), then fall back to system default
    exec(`code "${filePath}"`, (err) => {
      if (err) shell.openPath(filePath)
    })
    return { stdout: '', stderr: '', code: 0 }
  }
  return execApm(args)
})
