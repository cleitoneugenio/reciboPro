import { describe, it, expect } from 'vitest'
import { applyTemplate, formatCNPJ, valorPorExtenso } from '../src/shared/utils'

const WORKER = { name: 'João Silva', total: 500 }
const COMPANY = { name: 'Acme LTDA', cnpj: '12.345.678/0001-99', city: 'São Paulo', address: 'Rua das Flores, 123' }
const DATE = new Date(2026, 3, 23) // 23 de abril de 2026

// ── applyTemplate ────────────────────────────────────────────────────────────

describe('applyTemplate', () => {
  it('substitui [nome]', () => {
    expect(applyTemplate('[nome]', WORKER, COMPANY, DATE)).toBe('João Silva')
  })

  it('substitui [funcionario] sem acento', () => {
    expect(applyTemplate('[funcionario]', WORKER, COMPANY, DATE)).toBe('João Silva')
  })

  it('substitui [funcionário] com acento', () => {
    expect(applyTemplate('[funcionário]', WORKER, COMPANY, DATE)).toBe('João Silva')
  })

  it('substitui [total] com valor por extenso e formatação BRL', () => {
    const result = applyTemplate('[total]', WORKER, COMPANY, DATE)
    expect(result).toContain('R$ 500,00')
    expect(result).toContain('quinhentos reais')
  })

  it('substitui [valor] igual a [total]', () => {
    expect(applyTemplate('[valor]', WORKER, COMPANY, DATE)).toBe(
      applyTemplate('[total]', WORKER, COMPANY, DATE)
    )
  })

  it('substitui [empresa]', () => {
    expect(applyTemplate('[empresa]', WORKER, COMPANY, DATE)).toBe('Acme LTDA')
  })

  it('substitui [cnpj]', () => {
    expect(applyTemplate('[cnpj]', WORKER, COMPANY, DATE)).toBe('12.345.678/0001-99')
  })

  it('substitui [cidade]', () => {
    expect(applyTemplate('[cidade]', WORKER, COMPANY, DATE)).toBe('São Paulo')
  })

  it('substitui [endereco] sem acento', () => {
    expect(applyTemplate('[endereco]', WORKER, COMPANY, DATE)).toBe('Rua das Flores, 123')
  })

  it('substitui [endereço] com acento', () => {
    expect(applyTemplate('[endereço]', WORKER, COMPANY, DATE)).toBe('Rua das Flores, 123')
  })

  it('[endereco_completo] inclui vírgula quando endereço preenchido', () => {
    expect(applyTemplate('[endereco_completo]', WORKER, COMPANY, DATE)).toBe(', Rua das Flores, 123')
  })

  it('[endereco_completo] vazio quando endereço em branco', () => {
    const co = { ...COMPANY, address: '' }
    expect(applyTemplate('[endereco_completo]', WORKER, co, DATE)).toBe('')
  })

  it('substitui [data] com formato pt-BR', () => {
    expect(applyTemplate('[data]', WORKER, COMPANY, DATE)).toBe('23 de abril de 2026')
  })

  it('placeholders são case-insensitive', () => {
    expect(applyTemplate('[NOME]', WORKER, COMPANY, DATE)).toBe('João Silva')
    expect(applyTemplate('[Nome]', WORKER, COMPANY, DATE)).toBe('João Silva')
    expect(applyTemplate('[TOTAL]', WORKER, COMPANY, DATE)).toBe(applyTemplate('[total]', WORKER, COMPANY, DATE))
  })

  it('substitui múltiplos placeholders num mesmo template', () => {
    const result = applyTemplate('[nome] recebeu [total] de [empresa] em [cidade].', WORKER, COMPANY, DATE)
    expect(result).toContain('João Silva')
    expect(result).toContain('Acme LTDA')
    expect(result).toContain('São Paulo')
    expect(result).toContain('R$ 500,00')
  })

  it('substitui o mesmo placeholder que aparece múltiplas vezes', () => {
    const result = applyTemplate('[nome] — [nome]', WORKER, COMPANY, DATE)
    expect(result).toBe('João Silva — João Silva')
  })

  it('preserva texto sem placeholders intacto', () => {
    const template = 'Texto fixo sem variáveis nenhuma.'
    expect(applyTemplate(template, WORKER, COMPANY, DATE)).toBe(template)
  })

  it('template vazio retorna string vazia', () => {
    expect(applyTemplate('', WORKER, COMPANY, DATE)).toBe('')
  })

  it('total com centavos é formatado corretamente no template', () => {
    const w = { ...WORKER, total: 250.50 }
    const result = applyTemplate('[total]', w, COMPANY, DATE)
    expect(result).toContain('R$ 250,50')
    expect(result).toContain('duzentos e cinquenta reais')
    expect(result).toContain('cinquenta centavos')
  })
})

// ── formatCNPJ ───────────────────────────────────────────────────────────────

describe('formatCNPJ', () => {
  it('formata 14 dígitos no padrão XX.XXX.XXX/XXXX-XX', () => {
    expect(formatCNPJ('12345678000199')).toBe('12.345.678/0001-99')
  })

  it('ignora caracteres não numéricos no input', () => {
    expect(formatCNPJ('12.345.678/0001-99')).toBe('12.345.678/0001-99')
  })

  it('formata parcialmente: 2 dígitos', () => {
    expect(formatCNPJ('12')).toBe('12')
  })

  it('formata parcialmente: 5 dígitos — adiciona primeiro ponto', () => {
    expect(formatCNPJ('12345')).toBe('12.345')
  })

  it('formata parcialmente: 9 dígitos — abre barra', () => {
    expect(formatCNPJ('123456789')).toBe('12.345.678/9')
  })

  it('formata parcialmente: 12 dígitos — adiciona barra', () => {
    expect(formatCNPJ('123456780001')).toBe('12.345.678/0001')
  })

  it('formata parcialmente: 13 dígitos — barra sem traço', () => {
    expect(formatCNPJ('1234567800019')).toBe('12.345.678/0001-9')
  })

  it('trunca em 14 dígitos, ignora excedente', () => {
    expect(formatCNPJ('123456780001991234')).toBe('12.345.678/0001-99')
  })

  it('retorna vazio para input vazio', () => {
    expect(formatCNPJ('')).toBe('')
  })

  it('retorna vazio para input só com letras', () => {
    expect(formatCNPJ('abc')).toBe('')
  })
})

// ── valorPorExtenso — edge cases não cobertos antes ──────────────────────────

describe('valorPorExtenso — edge cases', () => {
  it('valor negativo retorna zero reais (guard Math.max)', () => {
    expect(valorPorExtenso(-100)).toBe('R$ 0,00 (zero reais)')
  })

  it('valor negativo fracionário retorna zero reais', () => {
    expect(valorPorExtenso(-0.01)).toBe('R$ 0,00 (zero reais)')
  })

  it('um milhão exato', () => {
    const result = valorPorExtenso(1_000_000)
    expect(result).toContain('um milhão')
    expect(result).toContain('R$ 1.000.000,00')
  })

  it('dois milhões', () => {
    expect(valorPorExtenso(2_000_000)).toContain('dois milhões')
  })

  it('milhão com resto', () => {
    const result = valorPorExtenso(1_500_000)
    expect(result).toContain('um milhão')
    expect(result).toContain('quinhentos mil')
  })

  it('valor muito grande não explode', () => {
    expect(() => valorPorExtenso(999_999_999)).not.toThrow()
  })
})
