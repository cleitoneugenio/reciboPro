import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { readSheets, readWorkers } from '../src/main/services/excel'
import ExcelJS from 'exceljs'
import { promises as fs } from 'fs'
import path from 'path'
import os from 'os'

const TEST_XLSX = path.join(os.tmpdir(), 'recibo-pro-test.xlsx')

beforeAll(async () => {
  const wb = new ExcelJS.Workbook()
  const ws = wb.addWorksheet('Semana 1')

  // header row
  ws.addRow(['#', 'Nome', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dias', 'Bonus', 'Total'])

  // workers (0-indexed col 10 = 1-indexed col 11 = Total)
  ws.addRow([1, 'João Silva', 100, 100, 100, 100, 'F', 100, 5, 0, 500])
  ws.addRow([2, 'Maria Santos', 150, 150, 150, 150, 150, 150, 6, 50, 950])
  ws.addRow([3, 'Pedro Costa', 0, 0, 0, 0, 0, 0, 0, 0, 0]) // total zero — deve ser ignorado
  ws.addRow([null, 'TOTAL GERAL', null, null, null, null, null, null, null, null, 1450]) // deve ser filtrado
  ws.addRow([null, 'Total da semana', null, null, null, null, null, null, null, null, 1450]) // deve ser filtrado

  const ws2 = wb.addWorksheet('Semana 2')
  ws2.addRow(['#', 'Nome', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dias', 'Bonus', 'Total'])
  ws2.addRow([1, 'Ana Lima', 200, 200, 200, 200, 200, 200, 6, 0, 1200])

  await wb.xlsx.writeFile(TEST_XLSX)
})

afterAll(async () => {
  await fs.unlink(TEST_XLSX).catch(() => undefined)
})

describe('readSheets', () => {
  it('retorna nomes das abas', async () => {
    const sheets = await readSheets(TEST_XLSX)
    expect(sheets).toEqual(['Semana 1', 'Semana 2'])
  })

  it('lança erro para arquivo inexistente', async () => {
    await expect(readSheets('/nao/existe.xlsx')).rejects.toThrow()
  })
})

describe('readWorkers', () => {
  it('lê funcionários com total > 0', async () => {
    const workers = await readWorkers(TEST_XLSX, 'Semana 1')
    expect(workers).toHaveLength(2)
    expect(workers[0]).toMatchObject({ name: 'João Silva', total: 500 })
    expect(workers[1]).toMatchObject({ name: 'Maria Santos', total: 950 })
  })

  it('ignora funcionários com total zero', async () => {
    const workers = await readWorkers(TEST_XLSX, 'Semana 1')
    expect(workers.every((w) => w.total > 0)).toBe(true)
  })

  it('lê aba alternativa', async () => {
    const workers = await readWorkers(TEST_XLSX, 'Semana 2')
    expect(workers).toHaveLength(1)
    expect(workers[0]).toMatchObject({ name: 'Ana Lima', total: 1200 })
  })

  it('lança erro para aba inexistente', async () => {
    await expect(readWorkers(TEST_XLSX, 'Semana 99')).rejects.toThrow('Semana 99')
  })

  it('filtra linhas cujo nome começa com "total" (case-insensitive)', async () => {
    const workers = await readWorkers(TEST_XLSX, 'Semana 1')
    const names = workers.map((w) => w.name.toLowerCase())
    expect(names.every((n) => !n.startsWith('total'))).toBe(true)
  })

  it('não inclui "TOTAL GERAL" na lista de funcionários', async () => {
    const workers = await readWorkers(TEST_XLSX, 'Semana 1')
    expect(workers.find((w) => /total/i.test(w.name))).toBeUndefined()
  })

  it('lê total formatado como texto de moeda "R$ 500,00"', async () => {
    const wb = new ExcelJS.Workbook()
    const currencyXlsx = path.join(os.tmpdir(), 'recibo-currency-test.xlsx')
    const ws = wb.addWorksheet('Moeda')
    ws.addRow(['#', 'Nome', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dias', 'Bonus', 'Total'])
    ws.addRow([1, 'Luisa Ramos', 100, 100, 100, 100, 100, 100, 6, 0, 'R$ 600,00'])
    ws.addRow([2, 'Bruno Melo', 150, 150, 150, 150, 150, 150, 6, 0, 'R$ 1.200,00'])
    ws.addRow([3, 'Carla Dias', 200, 200, 200, 200, 200, 200, 6, 0, 'R$ 1.234,56'])
    await wb.xlsx.writeFile(currencyXlsx)
    const workers = await readWorkers(currencyXlsx, 'Moeda')
    expect(workers).toHaveLength(3)
    expect(workers[0]).toMatchObject({ name: 'Luisa Ramos', total: 600 })
    expect(workers[1]).toMatchObject({ name: 'Bruno Melo', total: 1200 })
    expect(workers[2]).toMatchObject({ name: 'Carla Dias', total: 1234.56 })
    await fs.unlink(currencyXlsx).catch(() => undefined)
  })

  it('lê célula de fórmula corretamente', async () => {
    const wb = new ExcelJS.Workbook()
    const formulaXlsx = path.join(os.tmpdir(), 'recibo-formula-test.xlsx')
    const ws = wb.addWorksheet('Formulas')
    ws.addRow(['#', 'Nome', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dias', 'Bonus', 'Total'])
    const row = ws.addRow([1, 'Carlos Lima', 100, 100, 100, 100, 100, 100, 6, 0])
    row.getCell(11).value = { formula: 'SUM(C2:J2)', result: 700 }
    await wb.xlsx.writeFile(formulaXlsx)
    const workers = await readWorkers(formulaXlsx, 'Formulas')
    expect(workers).toHaveLength(1)
    expect(workers[0]).toMatchObject({ name: 'Carlos Lima', total: 700 })
    await fs.unlink(formulaXlsx).catch(() => undefined)
  })
})
