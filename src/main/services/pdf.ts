import { PDFDocument, StandardFonts, rgb, type PDFPage, type PDFFont } from 'pdf-lib'
import { promises as fs } from 'fs'
import type { GeneratePdfOptions, Worker, CompanyConfig } from '../../shared/types'
import { applyTemplate, DEFAULT_TEMPLATE, formatarData, valorPorExtenso } from '../../shared/utils'

// ── Constantes de layout A4 (em pontos PDF: 1pt = 1/72 polegada) ────────────
const A4_W = 595.28
const A4_H = 841.89
const MARGIN = 40       // margem externa do recibo na página
const RECEIPT_GAP = 20  // espaço vertical entre recibos na mesma página

// ── Paleta de cores ──────────────────────────────────────────────────────────
const BLACK      = rgb(0, 0, 0)
const GRAY       = rgb(0.4, 0.4, 0.4)
const LIGHT_GRAY = rgb(0.82, 0.82, 0.82)
const GREEN      = rgb(0.09, 0.64, 0.22) // cor do wordmark; não usada no corpo do recibo

/**
 * Calcula a altura disponível para cada recibo dado N recibos por página.
 * Desconta margens superior/inferior e os gaps entre recibos.
 */
function receiptHeight(n: number): number {
  return (A4_H - 2 * MARGIN - (n - 1) * RECEIPT_GAP) / n
}

/**
 * Quebra um texto em linhas que caibam dentro de `maxWidth` pontos,
 * respeitando fronteiras de palavras.
 *
 * @returns Array de strings, cada uma representando uma linha.
 */
function wrapText(text: string, font: PDFFont, fontSize: number, maxWidth: number): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let current = ''
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word
    if (font.widthOfTextAtSize(candidate, fontSize) <= maxWidth) {
      current = candidate
    } else {
      if (current) lines.push(current)
      current = word
    }
  }
  if (current) lines.push(current)
  return lines
}

/**
 * Desenha texto com quebra de linha automática em `page`.
 *
 * @param x        - Posição X inicial
 * @param y        - Posição Y inicial (decresce a cada linha)
 * @param maxWidth - Largura máxima antes de quebrar
 * @returns Y após a última linha desenhada.
 */
function drawWrapped(
  page: PDFPage, text: string, x: number, y: number,
  maxWidth: number, font: PDFFont, fontSize: number, lineHeight: number,
  color = BLACK,
): number {
  for (const line of wrapText(text, font, fontSize, maxWidth)) {
    page.drawText(line, { x, y, size: fontSize, font, color })
    y -= lineHeight
  }
  return y
}

/**
 * Desenha o corpo do recibo com o trecho do valor em negrito.
 *
 * Localiza `valueStr` dentro de `body` e renderiza:
 * - palavras antes do valor: Helvetica regular, preto
 * - palavras do valor: HelveticaBold, preto
 * - palavras após o valor: Helvetica regular, preto
 *
 * O word-wrap é feito palavra a palavra, considerando que bold e regular
 * têm larguras diferentes — sem isso, linhas com palavras mistas
 * transbordariam ou ficariam curtas.
 *
 * Se `valueStr` não for encontrado em `body`, cai em `drawWrapped` normal.
 *
 * @returns Y após a última linha desenhada.
 */
function drawBodyHighlighted(
  page: PDFPage, body: string, valueStr: string,
  x: number, startY: number, maxWidth: number,
  regular: PDFFont, bold: PDFFont,
  fontSize: number, lineHeight: number,
): number {
  const idx = body.indexOf(valueStr)
  if (idx === -1) return drawWrapped(page, body, x, startY, maxWidth, regular, fontSize, lineHeight)

  // Tokeniza o body em palavras marcadas como isValue ou não
  type Token = { word: string; isValue: boolean }
  const tokens: Token[] = []
  body.slice(0, idx).split(' ').filter(Boolean).forEach((w) => tokens.push({ word: w, isValue: false }))
  valueStr.split(' ').filter(Boolean).forEach((w) => tokens.push({ word: w, isValue: true }))
  body.slice(idx + valueStr.length).split(' ').filter(Boolean).forEach((w) => tokens.push({ word: w, isValue: false }))

  // Agrupa tokens em linhas respeitando maxWidth
  // O espaço entre palavras usa a largura do regular (espaço mais neutro)
  type Line = { word: string; isValue: boolean }[]
  const lines: Line[] = []
  let line: Line = []
  let lineW = 0

  for (const token of tokens) {
    const font = token.isValue ? bold : regular
    const spaceW = line.length > 0 ? regular.widthOfTextAtSize(' ', fontSize) : 0
    const wordW = font.widthOfTextAtSize(token.word, fontSize)
    if (lineW + spaceW + wordW > maxWidth && line.length > 0) {
      lines.push(line)
      line = [token]
      lineW = wordW
    } else {
      line.push(token)
      lineW += spaceW + wordW
    }
  }
  if (line.length > 0) lines.push(line)

  // Desenha cada linha palavra a palavra, avançando X conforme a largura real de cada fonte
  let y = startY
  for (const row of lines) {
    let xPos = x
    for (let i = 0; i < row.length; i++) {
      const { word, isValue } = row[i]!
      const prefix = i > 0 ? ' ' : ''
      const font = isValue ? bold : regular
      page.drawText(prefix + word, { x: xPos, y, size: fontSize, font, color: BLACK })
      xPos += font.widthOfTextAtSize(prefix + word, fontSize)
    }
    y -= lineHeight
  }
  return y
}

/**
 * Desenha um recibo completo dentro de uma área vertical delimitada por
 * `topY` (topo) e `topY - receiptH` (base).
 *
 * Estrutura visual (de cima para baixo):
 *   1. Borda retangular do recibo
 *   2. Cabeçalho: nome, CNPJ, endereço (cada campo é opcional via CompanyConfig)
 *   3. Divisor horizontal
 *   4. Título centralizado (ex: "RECIBO DE PRESTAÇÃO DE SERVIÇO")
 *   5. Divisor horizontal
 *   6. [opcional] Caixa de valor em destaque — label "VALOR" + montante em bold
 *   7. Corpo do recibo (texto por extenso com wrap; valor em bold se highlightValue)
 *   8. Linha de data
 *   9. Linha de assinatura centralizada
 *  10. Nome do funcionário centralizado abaixo da linha
 */
function drawReceipt(
  page: PDFPage, worker: Worker, company: CompanyConfig, date: Date,
  topY: number, receiptH: number, regular: PDFFont, bold: PDFFont,
): void {
  const left = MARGIN
  const right = A4_W - MARGIN
  const width = right - left
  const innerLeft = left + 14   // recuo interno para texto
  const innerWidth = width - 28 // largura útil para texto (14pt de cada lado)

  // Borda externa do recibo
  page.drawRectangle({
    x: left, y: topY - receiptH, width, height: receiptH,
    borderColor: LIGHT_GRAY, borderWidth: 0.5,
  })

  // Visibilidade individual de cada campo do cabeçalho
  const showName    = company.headerShowName    !== false
  const showCnpj    = company.headerShowCnpj    !== false
  const showAddress = company.headerShowAddress !== false
  const hasHeader   = showName || showCnpj || showAddress

  let y = topY - 22

  if (showName) {
    page.drawText(company.name.toUpperCase(), { x: innerLeft, y, size: 10, font: bold, color: BLACK })
    y -= 15
  }
  if (showCnpj) {
    page.drawText(`CNPJ: ${company.cnpj}`, { x: innerLeft, y, size: 8, font: regular, color: GRAY })
    y -= 12
  }
  if (showAddress) {
    const addressLine = [company.address, company.city].filter(Boolean).join(' — ')
    page.drawText(addressLine, { x: innerLeft, y, size: 8, font: regular, color: GRAY, maxWidth: innerWidth })
    y -= 16
  }

  if (hasHeader) {
    page.drawLine({ start: { x: left, y }, end: { x: right, y }, thickness: 0.5, color: LIGHT_GRAY })
    y -= 16
  } else {
    y -= 8
  }

  // Título — centralizado ou com valor inline dependendo de highlightValuePosition
  const title = (company.receiptTitle || 'RECIBO DE PRESTAÇÃO DE SERVIÇO').replace(/\s+/g, ' ').trim().toUpperCase()
  const inlineValue = company.highlightValue && company.highlightValuePosition === 'title'
  if (inlineValue) {
    // Título e valor usam o mesmo tamanho para harmonia visual
    const inlineSize = company.highlightValueSize ?? 9
    page.drawText(title, { x: innerLeft, y, size: inlineSize, font: bold, color: BLACK })
    const amountStr = valorPorExtenso(worker.total).split(' (')[0] ?? ''
    const amountW = bold.widthOfTextAtSize(amountStr, inlineSize)
    page.drawText(amountStr, { x: right - 14 - amountW, y, size: inlineSize, font: bold, color: BLACK })
  } else {
    const titleW = bold.widthOfTextAtSize(title, 9)
    page.drawText(title, { x: left + (width - titleW) / 2, y, size: 9, font: bold, color: BLACK })
  }
  y -= 14

  page.drawLine({ start: { x: left, y }, end: { x: right, y }, thickness: 0.5, color: LIGHT_GRAY })
  y -= 14

  // Caixa de valor em destaque (posição 'box', opcional)
  if (company.highlightValue && !inlineValue) {
    const boxH = 26
    page.drawRectangle({
      x: left, y: y - boxH, width, height: boxH,
      color: rgb(0.96, 0.96, 0.96),
      borderColor: rgb(0.88, 0.88, 0.88),
      borderWidth: 0.5,
    })
    page.drawText('VALOR', { x: innerLeft, y: y - boxH + 9, size: 7, font: bold, color: GRAY })
    const amountStr = valorPorExtenso(worker.total).split(' (')[0] ?? ''
    const amountSize = company.highlightValueSize ?? 12
    const amountW = bold.widthOfTextAtSize(amountStr, amountSize)
    page.drawText(amountStr, { x: right - 14 - amountW, y: y - boxH + (boxH - amountSize) / 2, size: amountSize, font: bold, color: BLACK })
    y = y - boxH - 14
  } else if (!company.highlightValue) {
    y -= 8
  }

  // Corpo do recibo: aplica template com substituição de placeholders
  // Normaliza whitespace — o template pode conter \n digitados pelo usuário;
  // pdf-lib/WinAnsi não suporta caracteres de controle em drawText.
  const template = company.receiptTemplate || DEFAULT_TEMPLATE
  const body = applyTemplate(template, worker, company, date).replace(/\s+/g, ' ').trim()
  const valueStr = valorPorExtenso(worker.total)
  y = company.highlightValue
    ? drawBodyHighlighted(page, body, valueStr, innerLeft, y, innerWidth, regular, bold, 10, 15.5)
    : drawWrapped(page, body, innerLeft, y, innerWidth, regular, 10, 15.5)
  y -= 32

  // Data
  page.drawText(`${company.city}, ${formatarData(date)}.`, { x: innerLeft, y, size: 9, font: regular, color: GRAY })
  y -= company.signatureSpacing ?? 44

  // Linha de assinatura centralizada (210pt de largura)
  const sigWidth = 210
  const sigX = left + (width - sigWidth) / 2
  page.drawLine({ start: { x: sigX, y }, end: { x: sigX + sigWidth, y }, thickness: 0.5, color: BLACK })
  y -= 13

  // Nome do funcionário centralizado abaixo da linha
  const nameW = regular.widthOfTextAtSize(worker.name, 9)
  page.drawText(worker.name, { x: sigX + (sigWidth - nameW) / 2, y, size: 9, font: regular, color: BLACK })
}

/**
 * Gera um arquivo PDF com os recibos de todos os `workers` fornecidos.
 *
 * Distribui os recibos em páginas A4, com `receiptsPerPage` recibos por página.
 * Cada página é adicionada automaticamente quando necessário.
 *
 * A data é aceita como `Date` ou string ISO — necessário porque o IPC serializa
 * objetos Date para string ao atravessar o contextBridge.
 *
 * @throws Error se `workers` estiver vazio.
 */
export async function generatePdf(options: GeneratePdfOptions): Promise<void> {
  const { workers, outputPath, company, receiptsPerPage = 2 } = options

  // Date vem como string ISO quando serializado pelo IPC (contextBridge não preserva Date)
  const rawDate = (options as GeneratePdfOptions & { date?: unknown }).date
  const date = rawDate instanceof Date ? rawDate : (rawDate ? new Date(rawDate as string) : new Date())

  const n = Math.max(1, Math.round(receiptsPerPage))

  if (workers.length === 0) throw new Error('Nenhum funcionário selecionado')

  const pdfDoc = await PDFDocument.create()
  const regular = await pdfDoc.embedFont(StandardFonts.Helvetica)
  const bold    = await pdfDoc.embedFont(StandardFonts.HelveticaBold)

  const rh = receiptHeight(n)
  let page: PDFPage | null = null
  let receiptOnPage = 0

  for (const worker of workers) {
    if (receiptOnPage === 0 || receiptOnPage >= n) {
      page = pdfDoc.addPage([A4_W, A4_H])
      receiptOnPage = 0
    }
    const topY = A4_H - MARGIN - receiptOnPage * (rh + RECEIPT_GAP)
    drawReceipt(page!, worker, company, date, topY, rh, regular, bold)
    receiptOnPage++
  }

  await fs.writeFile(outputPath, await pdfDoc.save())
}
