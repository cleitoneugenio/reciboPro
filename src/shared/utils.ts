// Utilitários PT-BR puros — sem deps Node.js, seguros no renderer e no main

const UNIDADES = [
  '', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove',
  'dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove',
]

const DEZENAS = [
  '', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa',
]

const CENTENAS = [
  '', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos',
  'seiscentos', 'setecentos', 'oitocentos', 'novecentos',
]

function abaixoDe1000(n: number): string {
  if (n === 0) return ''
  if (n < 20) return UNIDADES[n] ?? ''
  if (n < 100) {
    const d = Math.floor(n / 10)
    const u = n % 10
    return u === 0 ? (DEZENAS[d] ?? '') : `${DEZENAS[d]} e ${UNIDADES[u]}`
  }
  if (n === 100) return 'cem'
  const c = Math.floor(n / 100)
  const resto = n % 100
  const centena = CENTENAS[c] ?? ''
  if (resto === 0) return centena
  return `${centena} e ${abaixoDe1000(resto)}`
}

function numeroPorExtenso(n: number): string {
  if (n === 0) return 'zero'
  if (n < 1000) return abaixoDe1000(n)
  if (n < 1_000_000) {
    const mil = Math.floor(n / 1000)
    const resto = n % 1000
    const milStr = mil === 1 ? 'mil' : `${abaixoDe1000(mil)} mil`
    if (resto === 0) return milStr
    return `${milStr} e ${abaixoDe1000(resto)}`
  }
  const milh = Math.floor(n / 1_000_000)
  const resto = n % 1_000_000
  const milhStr = milh === 1 ? 'um milhão' : `${abaixoDe1000(milh)} milhões`
  if (resto === 0) return milhStr
  return `${milhStr} e ${numeroPorExtenso(resto)}`
}

function formatBRL(valor: number): string {
  const fixed = valor.toFixed(2)
  const [intPart = '0', decPart = '00'] = fixed.split('.')
  const intFormatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${intFormatted},${decPart}`
}

export function valorPorExtenso(valor: number): string {
  const rounded = Math.round(Math.max(0, valor) * 100) / 100
  const reais = Math.floor(rounded)
  const centavos = Math.round((rounded - reais) * 100)

  const parts: string[] = []
  if (reais > 0) parts.push(`${numeroPorExtenso(reais)} ${reais === 1 ? 'real' : 'reais'}`)
  if (centavos > 0) parts.push(`${numeroPorExtenso(centavos)} ${centavos === 1 ? 'centavo' : 'centavos'}`)
  if (parts.length === 0) parts.push('zero reais')

  return `R$ ${formatBRL(rounded)} (${parts.join(' e ')})`
}

const MESES = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]

export function formatCNPJ(value: string): string {
  const d = value.replace(/\D/g, '').slice(0, 14)
  return d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3})(\d)/, '$1/$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3}\/\d{4})(\d)/, '$1-$2')
}

export function formatarData(date: Date = new Date()): string {
  return `${date.getDate()} de ${MESES[date.getMonth()]} de ${date.getFullYear()}`
}

export const DEFAULT_TEMPLATE =
  'Recebi da [empresa] inscrita no [cnpj] o valor de [total] referente ao serviço de diárias na obra.'

export function applyTemplate(
  template: string,
  worker: { name: string; total: number },
  company: { name: string; cnpj: string; city: string; address: string },
  date: Date,
): string {
  const addressPart = company.address ? `, ${company.address}` : ''
  const totalExtenso = valorPorExtenso(worker.total)
  return template
    .replace(/\[nome\]/gi, worker.name)
    .replace(/\[funcionario\]/gi, worker.name)
    .replace(/\[funcionário\]/gi, worker.name)
    .replace(/\[total\]/gi, totalExtenso)
    .replace(/\[valor\]/gi, totalExtenso)
    .replace(/\[empresa\]/gi, company.name)
    .replace(/\[cnpj\]/gi, company.cnpj)
    .replace(/\[cidade\]/gi, company.city)
    .replace(/\[endereco\]/gi, company.address)
    .replace(/\[endereço\]/gi, company.address)
    .replace(/\[endereco_completo\]/gi, addressPart)
    .replace(/\[data\]/gi, formatarData(date))
}
