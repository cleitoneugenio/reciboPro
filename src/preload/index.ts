import { contextBridge, ipcRenderer, webUtils } from 'electron'
import type { CompanyConfig, GeneratePdfOptions, IpcResponse, Worker } from '../shared/types'

const api = {
  config: {
    get: (): Promise<IpcResponse<CompanyConfig | null>> =>
      ipcRenderer.invoke('config:get'),
    set: (config: CompanyConfig): Promise<IpcResponse> =>
      ipcRenderer.invoke('config:set', config),
  },
  recent: {
    get: (): Promise<IpcResponse<string[]>> =>
      ipcRenderer.invoke('recent:get'),
    add: (filePath: string): Promise<IpcResponse> =>
      ipcRenderer.invoke('recent:add', filePath),
  },
  excel: {
    readSheets: (filePath: string): Promise<IpcResponse<string[]>> =>
      ipcRenderer.invoke('excel:read-sheets', filePath),
    readWorkers: (filePath: string, sheetName: string): Promise<IpcResponse<Worker[]>> =>
      ipcRenderer.invoke('excel:read-workers', filePath, sheetName),
    samplePath: (): Promise<IpcResponse<string>> =>
      ipcRenderer.invoke('excel:sample-path'),
  },
  pdf: {
    generate: (options: GeneratePdfOptions): Promise<IpcResponse> =>
      ipcRenderer.invoke('pdf:generate', options),
  },
  dialog: {
    openXlsx: (): Promise<IpcResponse<string | null>> =>
      ipcRenderer.invoke('dialog:open-xlsx'),
    savePdf: (defaultName?: string): Promise<IpcResponse<string | null>> =>
      ipcRenderer.invoke('dialog:save-pdf', defaultName),
  },
  shell: {
    openPath: (filePath: string): Promise<IpcResponse> =>
      ipcRenderer.invoke('shell:open-path', filePath),
  },
  app: {
    getVersion: (): Promise<IpcResponse<string>> =>
      ipcRenderer.invoke('app:version'),
  },
  getPathForFile: (file: File): string => webUtils.getPathForFile(file),
}

contextBridge.exposeInMainWorld('api', api)

export type Api = typeof api
