import { app, BrowserWindow, nativeTheme } from 'electron'
import { join } from 'path'
import { registerHandlers } from './ipc/handlers'

const iconPath = join(__dirname, '../../resources/icon.ico')

const isDev = process.env['NODE_ENV'] === 'development'

function createWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1024,
    height: 680,
    minWidth: 780,
    minHeight: 540,
    backgroundColor: '#0F1F4D',
    icon: iconPath,
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0C1840',
      symbolColor: '#8FB3F0',
      height: 40,
    },
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true,
    },
  })

  win.on('ready-to-show', () => win.show())

  if (isDev && process.env['ELECTRON_RENDERER_URL']) {
    void win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    void win.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return win
}

app.whenReady().then(() => {
  nativeTheme.themeSource = 'dark'
  registerHandlers()
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
