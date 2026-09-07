import { describe, it, expect } from 'vitest'
import { valorPorExtenso, formatarData } from '../src/shared/utils'

describe('valorPorExtenso', () => {
  it('zero', () => {
    expect(valorPorExtenso(0)).toBe('R$ 0,00 (zero reais)')
  })

  it('valor inteiro simples', () => {
    expect(valorPorExtenso(1)).toBe('R$ 1,00 (um real)')
    expect(valorPorExtenso(2)).toBe('R$ 2,00 (dois reais)')
  })

  it('centenas exata — cem vs cento', () => {
    expect(valorPorExtenso(100)).toContain('cem reais')
    expect(valorPorExtenso(101)).toContain('cento e um reais')
  })

  it('centenas compostas', () => {
    expect(valorPorExtenso(250)).toContain('duzentos e cinquenta reais')
    expect(valorPorExtenso(999)).toContain('novecentos e noventa e nove reais')
  })

  it('mil exato', () => {
    expect(valorPorExtenso(1000)).toContain('mil reais')
  })

  it('mil e quinhentos', () => {
    expect(valorPorExtenso(1500)).toBe('R$ 1.500,00 (mil e quinhentos reais)')
  })

  it('dois mil', () => {
    expect(valorPorExtenso(2000)).toContain('dois mil reais')
  })

  it('valor com centavos', () => {
    expect(valorPorExtenso(250.5)).toBe('R$ 250,50 (duzentos e cinquenta reais e cinquenta centavos)')
  })

  it('apenas centavos', () => {
    expect(valorPorExtenso(0.01)).toBe('R$ 0,01 (um centavo)')
    expect(valorPorExtenso(0.5)).toBe('R$ 0,50 (cinquenta centavos)')
  })

  it('valor grande', () => {
    expect(valorPorExtenso(12500)).toContain('doze mil e quinhentos reais')
  })

  it('formatação BRL com separador de milhar', () => {
    expect(valorPorExtenso(1500)).toMatch(/R\$ 1\.500,00/)
    expect(valorPorExtenso(10000)).toMatch(/R\$ 10\.000,00/)
  })

  it('arredondamento correto', () => {
    // IEEE 754: 1.005 representa 1.00499..., arredonda para 1.00
    expect(valorPorExtenso(1.005)).toBe('R$ 1,00 (um real)')
    // valor sem ambiguidade de float
    expect(valorPorExtenso(1.02)).toBe('R$ 1,02 (um real e dois centavos)')
  })
})

describe('formatarData', () => {
  it('formata data em português', () => {
    const d = new Date(2026, 3, 21) // April = 3 (0-indexed)
    expect(formatarData(d)).toBe('21 de abril de 2026')
  })

  it('todos os meses', () => {
    const meses = [
      'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
      'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
    ]
    meses.forEach((mes, i) => {
      const d = new Date(2026, i, 1)
      expect(formatarData(d)).toContain(mes)
    })
  })
})
