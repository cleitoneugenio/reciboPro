import { ipcMain, dialog, shell, app } from 'electron'
import path from 'path'
import { readSheets, readWorkers } from '../services/excel'
import { generatePdf } from '../services/pdf'
import { getConfig, setConfig, getRecent, addRecent } from '../store'
import { ok, err } from '../../shared/types'
import type { CompanyConfig, GeneratePdfOptions, Worker } from '../../shared/types'

export function registerHandlers(): void {
  ipcMain.handle('config:get', async () => {
    try { return ok(await getConfig()) } catch (e) { return err(e) }
  })

  ipcMain.handle('config:set', async (_event, config: unknown) => {
    try {
      if (!isCompanyConfig(config)) return err('Configuração inválida')
      await setConfig(config)
      return ok(undefined)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('recent:get', async () => {
    try { return ok(await getRecent()) } catch (e) { return err(e) }
  })

  ipcMain.handle('recent:add', async (_event, filePath: unknown) => {
    try {
      if (typeof filePath !== 'string') return err('Caminho inválido')
      await addRecent(filePath)
      return ok(undefined)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('excel:read-sheets', async (_event, filePath: unknown) => {
    try {
      if (typeof filePath !== 'string') return err('Caminho inválido')
      return ok(await readSheets(filePath))
    } catch (e) { return err(e) }
  })

  ipcMain.handle('excel:read-workers', async (_event, filePath: unknown, sheetName: unknown) => {
    try {
      if (typeof filePath !== 'string' || typeof sheetName !== 'string') return err('Parâmetros inválidos')
      return ok(await readWorkers(filePath, sheetName))
    } catch (e) { return err(e) }
  })

  ipcMain.handle('excel:sample-path', () => {
    try {
      const file = 'exemplo-recibopro.xlsx'
      const p = app.isPackaged
        ? path.join(process.resourcesPath, file)
        : path.join(app.getAppPath(), 'resources', 'sample', file)
      return ok(p)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('pdf:generate', async (_event, options: unknown) => {
    try {
      if (!isGenerateOptions(options)) return err('Opções de PDF inválidas')
      await generatePdf(options)
      return ok(undefined)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('dialog:open-xlsx', async () => {
    try {
      const result = await dialog.showOpenDialog({
        title: 'Selecionar planilha',
        filters: [{ name: 'Planilha Excel', extensions: ['xlsx', 'xls'] }],
        properties: ['openFile'],
      })
      return ok(result.canceled ? null : (result.filePaths[0] ?? null))
    } catch (e) { return err(e) }
  })

  ipcMain.handle('dialog:save-pdf', async (_event, defaultName: unknown) => {
    try {
      const name = typeof defaultName === 'string' ? defaultName : 'recibos.pdf'
      const result = await dialog.showSaveDialog({
        title: 'Salvar recibos',
        defaultPath: path.join(app.getPath('documents'), name),
        filters: [{ name: 'PDF', extensions: ['pdf'] }],
      })
      return ok(result.canceled ? null : result.filePath)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('shell:open-path', async (_event, filePath: unknown) => {
    try {
      if (typeof filePath !== 'string') return err('Caminho inválido')
      await shell.openPath(filePath)
      return ok(undefined)
    } catch (e) { return err(e) }
  })

  ipcMain.handle('app:version', () => ok(app.getVersion()))
}

function isCompanyConfig(v: unknown): v is CompanyConfig {
  if (!v || typeof v !== 'object') return false
  const c = v as Record<string, unknown>
  return (
    typeof c['name'] === 'string' &&
    typeof c['cnpj'] === 'string' &&
    typeof c['address'] === 'string' &&
    typeof c['city'] === 'string' &&
    (c['headerShowName'] === undefined || typeof c['headerShowName'] === 'boolean') &&
    (c['headerShowCnpj'] === undefined || typeof c['headerShowCnpj'] === 'boolean') &&
    (c['headerShowAddress'] === undefined || typeof c['headerShowAddress'] === 'boolean') &&
    (c['receiptTitle'] === undefined || typeof c['receiptTitle'] === 'string') &&
    (c['receiptTemplate'] === undefined || typeof c['receiptTemplate'] === 'string') &&
    (c['signatureSpacing'] === undefined || typeof c['signatureSpacing'] === 'number') &&
    (c['highlightValue'] === undefined || typeof c['highlightValue'] === 'boolean') &&
    (c['highlightValueSize'] === undefined || typeof c['highlightValueSize'] === 'number') &&
    (c['highlightValuePosition'] === undefined || c['highlightValuePosition'] === 'box' || c['highlightValuePosition'] === 'title')
  )
}

function isWorker(v: unknown): v is Worker {
  if (!v || typeof v !== 'object') return false
  const w = v as Record<string, unknown>
  return typeof w['id'] === 'number' && typeof w['name'] === 'string' && typeof w['total'] === 'number'
}

function isGenerateOptions(v: unknown): v is GeneratePdfOptions {
  if (!v || typeof v !== 'object') return false
  const o = v as Record<string, unknown>
  return (
    Array.isArray(o['workers']) &&
    (o['workers'] as unknown[]).every(isWorker) &&
    typeof o['outputPath'] === 'string' &&
    isCompanyConfig(o['company'])
  )
}
