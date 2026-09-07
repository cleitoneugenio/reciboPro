import ExcelJS from 'exceljs'
import type { Worker } from '../../shared/types'

function parseCurrencyString(s: string): number {
  // Strip everything except digits, dot, and comma — handles "R$ 1.234,56", "R$ 500.00", "500"
  const cleaned = s.replace(/[^\d.,]/g, '')
  if (!cleaned) return NaN
  // BRL format uses comma as decimal separator and dot as thousands separator
  if (cleaned.includes(',')) {
    return Number(cleaned.replace(/\./g, '').replace(',', '.'))
  }
  // US/plain format: dots are thousands separators only when more than one, else decimal
  const dotCount = (cleaned.match(/\./g) ?? []).length
  if (dotCount > 1) return Number(cleaned.replace(/\./g, ''))
  return Number(cleaned)
}

function cellNumber(val: ExcelJS.CellValue): number {
  if (typeof val === 'number') return val
  if (typeof val === 'string') return parseCurrencyString(val)
  if (val !== null && typeof val === 'object') {
    // CellFormulaValue: { formula, result }
    if ('result' in val) {
      const r = (val as { result: unknown }).result
      if (typeof r === 'number') return r
      if (typeof r === 'string') return parseCurrencyString(r)
      return Number(r)
    }
  }
  return Number(val)
}

function cellString(val: ExcelJS.CellValue): string | null {
  if (typeof val === 'string') return val.trim() || null
  if (val !== null && typeof val === 'object') {
    // CellRichTextValue: { richText: [{text}] }
    if ('richText' in val) {
      const parts = (val as { richText: Array<{ text: string }> }).richText
      return parts.map((p) => p.text).join('').trim() || null
    }
    // CellFormulaValue com resultado string
    if ('result' in val) {
      const r = (val as { result: unknown }).result
      return typeof r === 'string' ? r.trim() || null : null
    }
  }
  if (val === null || val === undefined) return null
  return String(val).trim() || null
}

export async function readSheets(filePath: string): Promise<string[]> {
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.readFile(filePath)
  return workbook.worksheets.map((ws) => ws.name)
}

export async function readWorkers(filePath: string, sheetName: string): Promise<Worker[]> {
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.readFile(filePath)

  const sheet = workbook.getWorksheet(sheetName)
  if (!sheet) throw new Error(`Aba "${sheetName}" não encontrada`)

  const workers: Worker[] = []

  sheet.eachRow((row, rowNumber) => {
    if (rowNumber === 1) return

    const rawId = row.getCell(1).value
    const name = cellString(row.getCell(2).value)
    const total = cellNumber(row.getCell(11).value)
    const id = cellNumber(rawId)

    if (name && !isNaN(total) && total > 0 && !/^total/i.test(name)) {
      workers.push({ id: isNaN(id) ? rowNumber : id, name, total })
    }
  })

  return workers
}
