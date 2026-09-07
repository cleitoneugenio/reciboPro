export interface CompanyConfig {
  name: string
  cnpj: string
  address: string
  city: string
  headerShowName?: boolean
  headerShowCnpj?: boolean
  headerShowAddress?: boolean
  receiptTitle?: string
  receiptTemplate?: string
  signatureSpacing?: number
  highlightValue?: boolean
  highlightValueSize?: number
  highlightValuePosition?: 'box' | 'title'
}

export interface Worker {
  id: number
  name: string
  total: number
}

export interface GeneratePdfOptions {
  workers: Worker[]
  outputPath: string
  company: CompanyConfig
  date?: Date
  receiptsPerPage?: number
}

export interface IpcResult<T = void> {
  success: true
  data: T
}

export interface IpcError {
  success: false
  error: string
}

export type IpcResponse<T = void> = IpcResult<T> | IpcError

export function ok<T>(data: T): IpcResult<T> {
  return { success: true, data }
}

export function err(error: unknown): IpcError {
  const message = error instanceof Error ? error.message : String(error)
  return { success: false, error: message }
}
