# DOCUMENTAÇÃO TÉCNICA — reciboPro V2

![Ícone do reciboPro](recibo.png)

**Arquivo principal:** `src/` (monorepo Electron)
**Linguagem:** TypeScript 5.7 (strict mode)
**Runtime:** Electron 34.5.8 + React 19
**Produzido por:** HigherMind

Este documento explica passo a passo como a V2 do programa foi construída, o motivo de cada escolha técnica, como cada módulo funciona, bugs encontrados e como utilizá-lo no dia a dia.

---

## 1. OBJETIVO DO PROGRAMA

A V1 (Python + customtkinter) resolveu o problema para a GF MUNIZ ARTEFACTOS DE CERAMICA EIRELI: eliminar a criação manual de recibos toda semana. Funcionou — mas tinha um problema estrutural: os dados da empresa estavam **hardcoded** no código-fonte. Para usar em outra empresa, era necessário editar o arquivo `.py`, instalar Python e regerar o `.exe`.

**A V2 resolve isso:**

- Qualquer empresa pode configurar seus próprios dados (nome, CNPJ, cidade, endereço) pela interface gráfica
- O modelo do texto do recibo é editável com placeholders (`[nome]`, `[total]`, etc.)
- O cabeçalho é modular — o usuário escolhe o que aparece
- O executável é instalável via NSIS (instalador Windows padrão) com caminho para distribuição na Microsoft Store (MSIX)
- Zero dependência externa — o usuário final instala e usa, sem Python, sem pip, sem nada

**Problema resolvido:**
- V1 só servia para uma empresa específica
- V1 exigia Python instalado para rodar como script
- V1 não tinha onboarding — os dados eram constantes no código

**Solução entregue pela V2:**
- Onboarding na primeira execução: configura a empresa antes de usar
- Modelo do recibo personalizável via campo de texto com placeholders
- Cabeçalho configurável por toggles (nome, CNPJ, endereço)
- Espaçamento da linha de assinatura configurável por slider
- Preview ao vivo do recibo enquanto o usuário edita as configurações
- Instalador NSIS de um clique

---

## 2. DA V1 PARA A V2 — O QUE MUDOU E POR QUÊ

### 2.1 — Por que abandonar Python?

A V1 usava Python + customtkinter + PyInstaller. Funcionava, mas para distribuir um produto genérico havia limitações:

| Critério | V1 (Python) | V2 (Electron) |
|---|---|---|
| Interface | customtkinter (wrapper tkinter) | React 19 (HTML/CSS completo) |
| Distribuição | `.exe` único via PyInstaller | NSIS installer + Microsoft Store MSIX |
| Design | Widgets limitados ao tema CTk | CSS sem restrições — dark mode preciso |
| Web technologies | Não | Sim — HTML, CSS, JavaScript |
| Ecosistema de UI | Pequeno | Enorme (npm) |
| Tamanho do `.exe` | ~40 MB | ~87 MB (inclui Chromium) |

**Por que o tamanho maior vale a pena?** Porque em troca temos controle absoluto de pixel sobre o layout, tipografia editorial, transições, design system com CSS variables, e uma interface que pode evoluir indefinidamente sem limitações de widget.

**Interface da V1 em uso real (GF MUNIZ ARTEFACTOS DE CERAMICA EIRELI):**

![Interface V1 — Gerador de Recibos Python/customtkinter](scheenshot_gui.png.png)

*A V1 mostrava o logo Forte Telha hardcoded, a lista de funcionários com checkboxes, o preview do recibo ao lado, e o status "PDF gerado com sucesso." na parte inferior. Tudo funcional — mas amarrado a uma empresa específica.*

### 2.2 — Por que Electron e não Tauri?

Duas alternativas foram avaliadas:

- **Tauri** — usa Rust no backend + WebView do sistema operacional na frente. Executável pequeno (~5 MB). Mas exige Rust como linguagem de backend, o que adicionaria uma terceira linguagem ao projeto (Python V1 + TypeScript V2 + Rust Tauri).
- **Electron** — usa Node.js no backend + Chromium embutido. Executável maior (~87 MB), mas **TypeScript em todas as camadas** — main process, preload e renderer usam a mesma linguagem e os mesmos tipos.

**Decisão: Electron.** O ganho de consistência de linguagem e a maturidade do ecossistema superam a desvantagem do tamanho do executável.

### 2.3 — Por que reescrever a lógica em TypeScript e não usar o Python da V1 via subprocess?

Uma opção considerada foi manter o `gerar_recibos.py` da V1 e chamá-lo do Electron como um processo filho. Descartada por dois motivos:

1. Adicionaria dependência de Python instalado na máquina do usuário final (ou PyInstaller embutido no Electron, duplicando tamanho)
2. A lógica de negócio da V1 — `valor_por_extenso`, `formatar_data`, `ler_funcionarios` — é simples o suficiente para ser portada para TypeScript puro sem dependências pesadas

A portagem foi direta:
- `pandas.read_excel` → `exceljs`
- `reportlab` → `pdf-lib`
- `num2words` → implementação própria (arrays de extenso em português)
- `customtkinter` → React 19 + Tailwind CSS v4

---

## 3. TECNOLOGIAS UTILIZADAS

As versões exatas estão em `package.json`.

### 3.1 — Runtime e framework

| Biblioteca | Versão | Para que serve | Por que foi escolhida |
|---|---|---|---|
| `electron` | 34.5.8 | Runtime da aplicação — Node.js + Chromium | Maturidade, ecossistema, contextBridge para segurança |
| `react` | 19.0 | Interface declarativa | Versão mais recente; concurrent rendering; ecosystem |
| `typescript` | 5.7 | Tipagem estática em todo o projeto | Strict mode elimina erros de runtime; IntelliSense completo |
| `electron-vite` | 3.0 | Build tool — HMR + bundling para main/preload/renderer | Único tool que gerencia os 3 contextos do Electron nativamente |

### 3.2 — Interface

| Biblioteca | Versão | Para que serve | Por que foi escolhida |
|---|---|---|---|
| `tailwindcss` | 4.1 | Utilitários CSS + design system via `@theme` | V4 tem configuração CSS-first — sem `tailwind.config.js` |
| `@tailwindcss/vite` | 4.1 | Plugin Vite para processar Tailwind | Integração oficial V4 + Vite |
| `@fontsource-variable/inter` | 5.2.8 | Fonte Inter Variable (weight axis) | Zero request de rede; subsets automáticos; peso variável |
| `@vitejs/plugin-react` | 4.3 | Transformação JSX + React Refresh (HMR) | Plugin oficial React para Vite |

### 3.3 — Lógica de negócio

| Biblioteca | Versão | Para que serve | Por que foi escolhida |
|---|---|---|---|
| `exceljs` | 4.4.0 | Leitura de arquivos `.xlsx` | Único que expõe `CellFormulaValue.result` — necessário para planilhas com fórmulas |
| `pdf-lib` | 1.17.1 | Geração de PDF | Pure JS, zero deps nativas, controle total de coordenadas |

### 3.4 — Desenvolvimento e testes

| Biblioteca | Versão | Para que serve |
|---|---|---|
| `vitest` | 3.0 | Framework de testes — compatível com Vite |
| `jsdom` | 25.0 | Ambiente DOM para testes do renderer |
| `@testing-library/react` | 16.0 | Utilitários de teste para componentes React |
| `electron-builder` | 25.1.8 | Empacotamento e geração do instalador Windows |
| `prettier` | 3.3 | Formatação de código |
| `typescript-eslint` | 8.0 | Linting TypeScript |

---

## 4. ARQUITETURA GERAL

O Electron divide a aplicação em três contextos com responsabilidades distintas:

```
┌─────────────────────────────────────────────────────────┐
│  MAIN PROCESS (Node.js)                                 │
│  src/main/                                              │
│  ├── index.ts          — Cria janela, registra IPC      │
│  ├── store.ts          — Lê/escreve company.json        │
│  ├── ipc/handlers.ts   — Handlers de cada canal IPC     │
│  └── services/                                          │
│      ├── excel.ts      — Lê planilha .xlsx              │
│      └── pdf.ts        — Gera arquivo PDF               │
├─────────────────────────────────────────────────────────┤
│  PRELOAD (Bridge segura)                                │
│  src/preload/index.ts  — Expõe API tipada via           │
│                          contextBridge.exposeInMainWorld │
├─────────────────────────────────────────────────────────┤
│  RENDERER (Chromium + React)                            │
│  src/renderer/                                          │
│  ├── App.tsx           — Roteamento por estado          │
│  ├── pages/            — Main, Settings, Onboarding     │
│  └── components/       — ReceiptPreview, WorkerList     │
├─────────────────────────────────────────────────────────┤
│  SHARED (sem deps Node.js — seguro nos dois lados)      │
│  src/shared/                                            │
│  ├── types.ts          — Interfaces e IpcResponse<T>    │
│  └── utils.ts          — valorPorExtenso, applyTemplate │
└─────────────────────────────────────────────────────────┘
```

**Por que separar `src/shared/`?**
O código em `shared/` não pode importar módulos Node.js (`fs`, `path`, `exceljs`, etc.) nem APIs do browser (`window`, `document`). Só TypeScript puro. Isso permite que o renderer importe `applyTemplate` para o preview ao vivo, e o main process importe a mesma função para gerar o PDF — sem duplicação.

O alias `@shared` foi configurado em `electron.vite.config.ts` para evitar caminhos relativos frágeis (`../../shared/...`).

### 4.1 — Modelo de segurança

O Electron permite dois modos:

- **Inseguro:** `nodeIntegration: true` — o renderer tem acesso direto a Node.js. Risco: qualquer XSS tem acesso ao filesystem.
- **Seguro (escolhido):** `contextIsolation: true` + `nodeIntegration: false` — o renderer é isolado. Só acessa o que for explicitamente exposto via `contextBridge`.

```ts
// src/main/index.ts
webPreferences: {
  preload: join(__dirname, '../preload/index.js'),
  contextIsolation: true,
  nodeIntegration: false,
  sandbox: false,
  webSecurity: true,
}
```

**Por que `sandbox: false`?**
O Electron sandbox completo bloquearia o preload de usar Node.js internamente. Como o preload precisa de `ipcRenderer` (que é um módulo Electron/Node), mantemos `sandbox: false` enquanto preservamos `contextIsolation: true` — o nível de segurança correto para uma app desktop local.

---

## 5. ESTRUTURA DE ARQUIVOS

```
reciboPro/
├── src/
│   ├── main/
│   │   ├── index.ts              — Entry point do processo principal
│   │   ├── store.ts              — Persistência da config da empresa
│   │   ├── ipc/
│   │   │   └── handlers.ts       — Todos os handlers ipcMain.handle(...)
│   │   └── services/
│   │       ├── excel.ts          — readSheets(), readWorkers()
│   │       └── pdf.ts            — generatePdf()
│   ├── preload/
│   │   └── index.ts              — contextBridge.exposeInMainWorld('api', ...)
│   ├── renderer/
│   │   ├── index.html
│   │   └── src/
│   │       ├── App.tsx           — Router (loading / onboarding / main / settings)
│   │       ├── pages/
│   │       │   ├── Main.tsx      — Tela principal
│   │       │   ├── Settings.tsx  — Configurações da empresa
│   │       │   └── Onboarding.tsx — Primeira configuração
│   │       ├── components/
│   │       │   ├── ReceiptPreview.tsx — Preview HTML do recibo
│   │       │   └── WorkerList.tsx    — Lista de funcionários com checkboxes
│   │       └── styles/
│   │           └── globals.css   — Design system (@theme + animações)
│   └── shared/
│       ├── types.ts              — Interfaces + IpcResponse<T>
│       └── utils.ts              — Utilitários PT-BR puros
├── tests/
│   ├── utils.test.ts             — 35 testes (applyTemplate, formatCNPJ, valorPorExtenso)
│   └── excel.test.ts             — Testes de leitura do .xlsx
├── electron.vite.config.ts       — Build config (3 entrypoints + aliases)
├── electron-builder.yml          — Config do instalador Windows (NSIS + MSIX)
├── package.json
└── tsconfig.json                 — Referência para tsconfig.node + tsconfig.web
```

---

## 6. TIPOS COMPARTILHADOS — `src/shared/types.ts`

Define as estruturas de dados usadas em todo o projeto e o padrão de resposta IPC.

### 6.1 — CompanyConfig

```ts
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
}
```

**Por que campos opcionais com `?`?**
Os campos obrigatórios (`name`, `cnpj`, `address`, `city`) são os dados mínimos para gerar um recibo. Os opcionais têm defaults no código: se `headerShowName` é `undefined`, trata como `true`; se `receiptTemplate` é `undefined`, usa o `DEFAULT_TEMPLATE`; se `signatureSpacing` é `undefined`, usa `44`; se `highlightValue` é `undefined`, trata como `false`. Isso permite que configs salvas em versões anteriores continuem funcionando sem precisar de migração.

### 6.2 — Padrão IpcResponse\<T\>

```ts
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
```

**Por que esse padrão?**
O IPC do Electron serializa as respostas como JSON. Se um handler jogar uma exceção, o Electron a serializa como string vazia — a informação do erro se perde. Ao envolver toda resposta em `IpcResponse<T>`, o renderer sempre recebe um objeto com `success: boolean`. Erros nunca são silenciosos.

O TypeScript discrimina a union automaticamente:
```ts
const res = await window.api.config.get()
if (res.success) {
  // TypeScript sabe que res.data é CompanyConfig | null aqui
} else {
  // TypeScript sabe que res.error é string aqui
}
```

---

## 7. UTILITÁRIOS PT-BR — `src/shared/utils.ts`

Funções puras sem dependências externas. Portadas da V1 (Python) para TypeScript.

### 7.1 — valorPorExtenso(valor)

Recebe um número (ex: 395.50) e retorna a string completa formatada:
`"R$ 395,50 (trezentos e noventa e cinco reais e cinquenta centavos)"`

```ts
export function valorPorExtenso(valor: number): string {
  const rounded = Math.round(Math.max(0, valor) * 100) / 100
  const reais = Math.floor(rounded)
  const centavos = Math.round((rounded - reais) * 100)

  const parts: string[] = []
  if (reais > 0)    parts.push(`${numeroPorExtenso(reais)} ${reais === 1 ? 'real' : 'reais'}`)
  if (centavos > 0) parts.push(`${numeroPorExtenso(centavos)} ${centavos === 1 ? 'centavo' : 'centavos'}`)
  if (parts.length === 0) parts.push('zero reais')

  return `R$ ${formatBRL(rounded)} (${parts.join(' e ')})`
}
```

**Por que reimplementar em vez de usar uma lib como `num2words`?**
Na V1 em Python, `num2words` era a escolha natural. No TypeScript, as alternativas para pt-BR são desatualizadas ou pesadas. A lógica é simples: três arrays (`UNIDADES`, `DEZENAS`, `CENTENAS`) e recursão. Implementar internamente elimina uma dependência npm, reduz o bundle e garante comportamento 100% previsível.

**Por que `Math.max(0, valor)` antes de tudo?**
Protege contra valores negativos (ex: digitação incorreta). A V1 não tinha esse guard — adicionado na V2 após os testes identificarem o edge case.

**Por que `Math.round(... * 100) / 100`?**
Ponto flutuante em JavaScript: `0.1 + 0.2 === 0.30000000000000004`. Para valores monetários com centavos, arredondamos ao centavo antes de qualquer cálculo para evitar erros de precisão.

**Por que a formatação BRL manual?**
```ts
function formatBRL(valor: number): string {
  const [intPart = '0', decPart = '00'] = valor.toFixed(2).split('.')
  const intFormatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${intFormatted},${decPart}`
}
```
O `Intl.NumberFormat` com `pt-BR` formata corretamente no browser, mas no processo main do Electron (Node.js) o comportamento varia com o locale do sistema operacional. A implementação manual garante `R$ 1.234,56` independente do locale do Windows configurado na máquina do usuário.

### 7.2 — formatarData(date)

```ts
const MESES = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]

export function formatarData(date: Date = new Date()): string {
  return `${date.getDate()} de ${MESES[date.getMonth()]} de ${date.getFullYear()}`
}
```

**Por que a lista manual de meses?**
Idêntica à V1. O `Date.toLocaleDateString('pt-BR', { ... })` depende do locale do sistema. Em Windows configurados com locale diferente de pt-BR, retorna nomes de meses em outro idioma. A lista manual garante português independente do sistema.

### 7.3 — formatCNPJ(value)

```ts
export function formatCNPJ(value: string): string {
  const d = value.replace(/\D/g, '').slice(0, 14)
  return d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3})(\d)/, '$1/$2')
    .replace(/^(\d{2}\.\d{3}\.\d{3}\/\d{4})(\d)/, '$1-$2')
}
```

**Por que formatação progressiva com regex em cadeia?**
O campo CNPJ nas configurações usa esta função no `onChange` — formata enquanto o usuário digita. A cadeia de `.replace()` transforma qualquer sequência de dígitos no formato `XX.XXX.XXX/XXXX-XX` progressivamente: com 2 dígitos exibe `12`, com 5 exibe `12.345`, com 9 exibe `12.345.678/9`, etc. Cada regex aplica apenas se os dígitos necessários já existem.

### 7.4 — DEFAULT_TEMPLATE e applyTemplate()

```ts
export const DEFAULT_TEMPLATE =
  'Recebi da empresa [empresa], pessoa jurídica de direito privado, ' +
  'inscrita no CNPJ sob o n [cnpj], com sede na cidade de [cidade][endereco_completo], ' +
  'a quantia de [total]. Referente a serviço de diárias no dia [data]. ' +
  'Dando-lhe por este recibo a devida quitação.'

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
```

**Por que a flag `/gi` em todos os replaces?**
`g` = substituir todas as ocorrências (não só a primeira). `i` = case-insensitive — `[NOME]`, `[Nome]` e `[nome]` funcionam. O usuário que digitar o template não precisa saber sobre maiúsculas.

**Por que `[endereco_completo]` além de `[endereco]`?**
`[endereco]` retorna só o endereço, sem vírgula precedente. `[endereco_completo]` retorna `, Rua das Flores, 123` (com vírgula) se o endereço estiver preenchido, ou string vazia se não. Isso permite escrever `cidade de [cidade][endereco_completo]` no template — a vírgula aparece automaticamente só quando há endereço.

**Por que a mesma função no renderer e no main?**
`applyTemplate` é chamada no renderer para renderizar o preview HTML em tempo real, e no main para gerar o texto do PDF. Como está em `src/shared/utils.ts` (sem imports Node.js), funciona nos dois contextos — mesma lógica, sem duplicação.

---

## 8. LEITURA DO EXCEL — `src/main/services/excel.ts`

### 8.1 — Por que exceljs e não xlsx (SheetJS)?

Duas bibliotecas foram avaliadas:

| Critério | `exceljs` | `xlsx` (SheetJS) |
|---|---|---|
| CellFormulaValue | Expõe `.result` tipado | Retorna o valor calculado diretamente |
| CellRichTextValue | Expõe `.richText[].text` tipado | Pode retornar objeto opaco |
| TypeScript types | Incluídos no pacote | Separados (`@types/xlsx`) |
| Leitura de fórmulas | `{ formula: 'SUM(C2:J2)', result: 700 }` | Depende de `cellFormula`/`cellNF` flags |

A planilha da GF MUNIZ usa fórmulas na coluna TOTAL (`=SUM(C2:J2)`). O `exceljs` expõe o resultado calculado via `CellFormulaValue.result` de forma explícita e tipada.

### 8.2 — cellNumber() e cellString()

O exceljs usa `CellValue` como union de vários tipos possíveis. Foi necessário criar funções auxiliares para extrair o valor real:

```ts
function parseCurrencyString(s: string): number {
  // Suporta "R$ 1.234,56", "R$ 500,00", "500" — remove tudo exceto dígitos, ponto e vírgula
  const cleaned = s.replace(/[^\d.,]/g, '')
  if (!cleaned) return NaN
  // Formato BRL: vírgula como separador decimal, ponto como milhar
  if (cleaned.includes(',')) return Number(cleaned.replace(/\./g, '').replace(',', '.'))
  // Formato plain: múltiplos pontos = separadores de milhar
  const dotCount = (cleaned.match(/\./g) ?? []).length
  if (dotCount > 1) return Number(cleaned.replace(/\./g, ''))
  return Number(cleaned)
}

function cellNumber(val: ExcelJS.CellValue): number {
  if (typeof val === 'number') return val
  if (typeof val === 'string') return parseCurrencyString(val)
  if (val !== null && typeof val === 'object') {
    if ('result' in val) {              // CellFormulaValue
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
    if ('richText' in val) {            // CellRichTextValue
      const parts = (val as { richText: Array<{ text: string }> }).richText
      return parts.map((p) => p.text).join('').trim() || null
    }
    if ('result' in val) {              // CellFormulaValue com string
      const r = (val as { result: unknown }).result
      return typeof r === 'string' ? r.trim() || null : null
    }
  }
  if (val === null || val === undefined) return null
  return String(val).trim() || null
}
```

**Por que verificar `'result' in val` e `'richText' in val`?**
TypeScript não permite narrowing direto de union types que incluem interfaces (seria necessário um type guard completo). O operador `in` verifica a presença da chave no objeto em runtime — forma segura e idiomática de distinguir os subtipos do `CellValue`.

### 8.3 — readWorkers()

```ts
sheet.eachRow((row, rowNumber) => {
  if (rowNumber === 1) return  // cabeçalho

  const name  = cellString(row.getCell(2).value)
  const total = cellNumber(row.getCell(11).value)
  const id    = cellNumber(row.getCell(1).value)

  if (name && !isNaN(total) && total > 0 && !/^total/i.test(name)) {
    workers.push({ id: isNaN(id) ? rowNumber : id, name, total })
  }
})
```

**Por que `/^total/i.test(name)`?**
A planilha tem uma linha de rodapé como "TOTAL GERAL" ou "Total da semana" que soma os valores de todos os funcionários. Se essa linha fosse incluída, geraria um recibo para "TOTAL GERAL" com o valor somado da semana — um bug silencioso. O regex filtra qualquer linha cujo nome começa com "total" (case-insensitive).

**Por que `total > 0`?**
Funcionário que não trabalhou nenhum dia fica com total zero. Não faz sentido gerar recibo de R$ 0,00. Mesmo comportamento da V1.

**Por que `id: isNaN(id) ? rowNumber : id`?**
Se a coluna 1 tiver um número inteiro (número do funcionário), usa como ID. Se tiver texto ou estar vazia, usa o número da linha como fallback — garante que todo worker tem um ID único para o React (`key={w.id}`).

---

## 9. GERAÇÃO DO PDF — `src/main/services/pdf.ts`

### 9.1 — Por que pdf-lib e não ReportLab / jsPDF / Puppeteer?

| Biblioteca | Linguagem | Abordagem | Por que descartada |
|---|---|---|---|
| ReportLab | Python | Flowables | V2 é TypeScript — não aplicável |
| jsPDF | JS | Coordenadas + auto-layout | Menos tipagem; API mais verbosa |
| Puppeteer | JS | Renderiza HTML → PDF via Chromium headless | 200+ MB só do Chromium; inaceitável embutir outro Chromium dentro do Electron |
| **pdf-lib** | **JS** | **Coordenadas absolutas** | **Pure JS, zero deps nativas, tipagem excelente, controle preciso** |

**Por que coordenadas absolutas em vez de flowables (como ReportLab)?**
O layout do recibo é fixo — sempre o mesmo: cabeçalho, título, corpo, data, assinatura. Não há texto que flui entre páginas. Coordenadas absolutas são mais simples para layouts fixos e eliminam o overhead do motor de flowables.

### 9.2 — Dimensões e cálculo de layout

```ts
const A4_W = 595.28   // pontos PDF (1pt = 1/72 polegada)
const A4_H = 841.89
const MARGIN = 40
const RECEIPT_GAP = 20

function receiptHeight(n: number): number {
  return (A4_H - 2 * MARGIN - (n - 1) * RECEIPT_GAP) / n
}
```

**Por que pontos e não pixels ou mm?**
O PDF usa pontos como unidade nativa (1pt = 1/72"). O `pdf-lib` trabalha diretamente em pontos. Converter para mm e depois de volta adicionaria imprecisão de ponto flutuante sem benefício.

**Por que a fórmula `receiptHeight(n)`?**
Para `n` recibos por página:
- Espaço disponível: `A4_H - 2 * MARGIN` (subtrai margens top e bottom)
- Gaps entre recibos: `(n - 1) * RECEIPT_GAP` (n recibos criam n-1 gaps)
- Altura de cada recibo: divide o restante igualmente

Com `n=2`: `(841.89 - 80 - 20) / 2 = 370.95pt` por recibo.
Com `n=3`: `(841.89 - 80 - 40) / 3 = 240.63pt` por recibo.

### 9.3 — wrapText() e drawWrapped()

O `pdf-lib` não faz quebra automática de linha. Foi necessário implementar:

```ts
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
```

**Por que `font.widthOfTextAtSize()`?**
Cada fonte tem métricas diferentes — um caractere "W" é muito mais largo que um "i". Medir a largura real via a API da fonte garante que nenhuma linha ultrapasse a margem, independente do conteúdo do template personalizado.

### 9.4 — Cabeçalho condicional

```ts
const showName    = company.headerShowName    !== false
const showCnpj    = company.headerShowCnpj    !== false
const showAddress = company.headerShowAddress !== false
const hasHeader   = showName || showCnpj || showAddress
```

**Por que `!== false` em vez de `=== true`?**
O campo é opcional — pode ser `undefined` (config antiga sem essa preferência salva). Com `!== false`, `undefined` é tratado como `true` (mostrar por padrão). Com `=== true`, `undefined` seria tratado como `false` (esconder por padrão) — o que quebraria configs existentes.

### 9.5 — Assinatura centralizada

```ts
const sigWidth = 210
const sigX = left + (width - sigWidth) / 2

page.drawLine({ start: { x: sigX, y }, end: { x: sigX + sigWidth, y }, ... })

const nameW = regular.widthOfTextAtSize(worker.name, 9)
page.drawText(worker.name, { x: sigX + (sigWidth - nameW) / 2, y: y - 13, ... })
```

**Por que dois níveis de centralização?**
1. A linha de assinatura (`sigWidth = 210pt`) é centralizada na largura total do recibo
2. O nome do funcionário é centralizado dentro dessa linha de 210pt

Isso garante que nomes curtos ("Ana") e longos ("Francisco Rodrigues da Silva Neto") ficam sempre centralizados na mesma linha, sem quebrar o alinhamento visual.

### 9.6 — drawBodyHighlighted() — word-wrap com destaque do valor

Quando `company.highlightValue = true`, o valor por extenso no corpo do recibo é renderizado em negrito (Helvetica Bold) enquanto o restante do texto fica em regular. O desafio é que as duas fontes têm larguras diferentes — a mesma string é mais larga em Bold do que em Regular.

```ts
function drawBodyHighlighted(
  page, body, valueStr,
  x, startY, maxWidth,
  regular, bold,
  fontSize, lineHeight,
): number {
  // 1. Tokeniza o body em palavras marcadas como isValue ou não
  type Token = { word: string; isValue: boolean }
  const tokens: Token[] = []
  body.slice(0, idx).split(' ').filter(Boolean).forEach((w) =>
    tokens.push({ word: w, isValue: false }))
  valueStr.split(' ').filter(Boolean).forEach((w) =>
    tokens.push({ word: w, isValue: true }))
  body.slice(idx + valueStr.length).split(' ').filter(Boolean).forEach((w) =>
    tokens.push({ word: w, isValue: false }))

  // 2. Agrupa tokens em linhas respeitando maxWidth
  //    Espaço entre palavras usa largura do regular (neutro)
  for (const token of tokens) {
    const font = token.isValue ? bold : regular
    const spaceW = line.length > 0 ? regular.widthOfTextAtSize(' ', fontSize) : 0
    const wordW = font.widthOfTextAtSize(token.word, fontSize)
    if (lineW + spaceW + wordW > maxWidth && line.length > 0) {
      lines.push(line); line = [token]; lineW = wordW
    } else {
      line.push(token); lineW += spaceW + wordW
    }
  }

  // 3. Desenha cada linha palavra a palavra, avançando X pela largura real de cada fonte
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
}
```

**Por que tokenizar por palavra e não por caractere?**
Se medíssemos caractere por caractere, quebraríamos uma palavra no meio ao final da linha. Quebrando por palavra, cada unidade visual (uma palavra) vai inteira para a linha ou para a próxima.

**Por que usar `regular.widthOfTextAtSize(' ', fontSize)` para o espaço entre palavras?**
O espaço é o separador entre palavras de diferentes fontes. Usar a largura do Regular como espaço neutro mantém o ritmo visual consistente — um espaço Bold seria mais estreito que o Regular, criando inconsistência visual.

**Por que medir cada palavra com sua própria fonte antes de decidir se cabe na linha?**
Se usássemos apenas a fonte Regular para medir as palavras Bold, subestimaríamos a largura real — as linhas transbordariam o `maxWidth`. Medir com `font.widthOfTextAtSize` da fonte correta garante que cada linha cabe exatamente dentro da borda do recibo.

### 9.7 — Caixa de valor em destaque (highlightValue)

Quando `company.highlightValue = true`, uma caixa cinza clara é renderizada entre o título e o corpo do recibo, exibindo o label "VALOR" à esquerda e o montante numérico em Bold à direita:

```ts
if (company.highlightValue) {
  const boxH = 26
  page.drawRectangle({
    x: left, y: y - boxH, width, height: boxH,
    color: rgb(0.96, 0.96, 0.96),
    borderColor: rgb(0.88, 0.88, 0.88),
    borderWidth: 0.5,
  })
  page.drawText('VALOR', { x: innerLeft, y: y - boxH + 9, size: 7, font: bold, color: GRAY })
  // Exibe a parte numérica (antes do parêntese com extenso)
  const amountStr = valorPorExtenso(worker.total).split(' (')[0] ?? ''
  const amountW = bold.widthOfTextAtSize(amountStr, 12)
  page.drawText(amountStr, { x: right - 14 - amountW, y: y - boxH + 7, size: 12, font: bold, color: BLACK })
  y = y - boxH - 14
}
```

**Por que `split(' (')[0]`?**
`valorPorExtenso` retorna `"R$ 395,00 (trezentos e noventa e cinco reais)"`. A caixa de destaque mostra apenas o valor numérico formatado (`"R$ 395,00"`) — o extenso já aparece no corpo do recibo. O split no ` (` separa os dois.

**Por que `right - 14 - amountW` para posicionar?**
O valor é alinhado à direita dentro da caixa: parte da posição `right` (margem direita), subtrai 14pt de padding interno, e recua mais `amountW` (a largura do texto) — resultado: o final do texto fica exatamente a 14pt da borda direita do recibo.

---

## 10. CONFIGURAÇÃO PERSISTENTE — `src/main/store.ts`

```ts
function configPath(): string {
  return path.join(app.getPath('userData'), 'company.json')
}
```

**Por que `app.getPath('userData')`?**
No Windows, retorna `C:\Users\<user>\AppData\Roaming\recibo-pro\`. É o local correto para dados de aplicação por usuário — sempre gravável, nunca em `Program Files`. O Electron gerencia automaticamente o nome da pasta com base no `appId` do `electron-builder.yml`.

### Arquivos persistidos

| Arquivo | Conteúdo |
|---|---|
| `company.json` | `CompanyConfig` serializado — nome, CNPJ, endereço, template, etc. |
| `recent.json` | Array de strings (paths), máximo 5 entradas |

**recent.json — histórico de arquivos recentes:**

```ts
// Leitura
export async function getRecent(): Promise<string[]> {
  try {
    const data = await fs.readFile(recentPath(), 'utf-8')
    const parsed = JSON.parse(data)
    return Array.isArray(parsed) ? parsed.filter(p => typeof p === 'string') : []
  } catch { return [] }
}

// Adição (mantém máx. 5, sem duplicatas, mais recente primeiro)
export async function addRecent(filePath: string): Promise<void> {
  const existing = await getRecent()
  const updated = [filePath, ...existing.filter(p => p !== filePath)].slice(0, 5)
  await fs.writeFile(recentPath(), JSON.stringify(updated))
}
```

**Por que máximo 5 entradas?**
Arquivos recentes servem para acesso rápido — mais de 5 começa a parecer uma lista de arquivos, não atalhos rápidos. 5 é o padrão de aplicações como VS Code e Figma.

**Por que remover duplicatas antes de adicionar?**
Se o usuário abrir o mesmo arquivo duas vezes, ele deve aparecer uma vez — no topo (acesso mais recente). Filtrar antes de prepend garante isso sem lógica extra.

**Validação estrutural na leitura:**

```ts
const parsed = JSON.parse(data)
if (
  !parsed || typeof parsed !== 'object' ||
  typeof parsed.name !== 'string'     ||
  typeof parsed.cnpj !== 'string'     ||
  typeof parsed.city !== 'string'
) return null
return parsed as CompanyConfig
```

**Por que validar antes de fazer cast?**
Se o arquivo `company.json` estiver corrompido, truncado ou de uma versão incompatível, `JSON.parse` retorna algo inesperado. Sem validação, um cast direto (`as CompanyConfig`) passaria silenciosamente e causaria crashes em runtime quando o código tentasse acessar `company.name.toUpperCase()`. A validação retorna `null` para configs inválidas — o App.tsx redireciona para o Onboarding.

---

## 11. IPC — COMUNICAÇÃO ENTRE PROCESSOS

### 11.1 — Por que IPC e não acesso direto?

No Electron, o renderer (React) roda em um contexto Chromium isolado. Ele não pode acessar `fs`, `path`, `exceljs` ou qualquer API Node.js diretamente. A comunicação acontece via IPC (Inter-Process Communication):

```
Renderer  →  ipcRenderer.invoke('canal', dados)
                    ↓ (serialização JSON)
Main      →  ipcMain.handle('canal', async (event, dados) => resultado)
                    ↓ (serialização JSON)
Renderer  ←  resultado
```

### 11.2 — Preload como bridge tipada

```ts
// src/preload/index.ts
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
  app: {
    getVersion: (): Promise<IpcResponse<string>> =>
      ipcRenderer.invoke('app:version'),
  },
  getPathForFile: (file: File): string => webUtils.getPathForFile(file),
  // ...
}

contextBridge.exposeInMainWorld('api', api)
```

**Por que o padrão `namespace:ação`?**
`config:get`, `excel:read-sheets`, `pdf:generate`, `recent:get`, `app:version`. O prefixo de namespace agrupa handlers por domínio e previne colisão de nomes. Se eventualmente houver `dialog:open-xlsx` e `excel:open-xlsx`, ficam claramente distintos.

**Por que `app:version` via IPC e não embutido no bundle?**
A versão do app vive no `package.json` e é injetada pelo Electron em `app.getVersion()` no processo main — o único lugar onde é authoritative. Embuti-la no renderer via build (ex: `import pkg from '../../../package.json'`) criaria uma segunda fonte da verdade que pode desincronizar em builds parciais. O IPC garante que o renderer sempre mostra a versão real do binário em execução.

**Por que expor como objeto aninhado em vez de funções planas?**
`window.api.excel.readWorkers(path, sheet)` em vez de `window.readWorkers(path, sheet)`. O objeto aninhado organiza a API, permite IntelliSense por contexto e evita poluição do `window` global.

### 11.3 — Validação no handler

```ts
ipcMain.handle('config:set', async (_event, config: unknown) => {
  try {
    if (!isCompanyConfig(config)) return err('Configuração inválida')
    await setConfig(config)
    return ok(undefined)
  } catch (e) { return err(e) }
})
```

**Por que validar o argumento como `unknown`?**
O IPC serializa/deserializa via JSON. O TypeScript não pode garantir o tipo do que chega — qualquer coisa pode ser enviada do renderer. `isCompanyConfig()` valida em runtime cada campo necessário antes de persistir.

### 11.4 — `excel:sample-path` — planilha de exemplo embutida

Para tornar o app testável sem nenhuma dependência externa (ver §19), uma planilha de exemplo é empacotada **dentro** do app e exposta por um handler que resolve seu caminho em runtime:

```ts
ipcMain.handle('excel:sample-path', () => {
  const file = 'exemplo-recibopro.xlsx'
  const p = app.isPackaged
    ? path.join(process.resourcesPath, file)
    : path.join(app.getAppPath(), 'resources', 'sample', file)
  return ok(p)
})
```

**Por que resolver o caminho no main e não no renderer?**
Só o processo main conhece `process.resourcesPath` (onde o `extraResources` deposita o arquivo no app empacotado) e `app.isPackaged` (para distinguir dev de produção). O renderer recebe apenas o caminho final e o reaproveita no fluxo normal: `excel.samplePath()` → `loadFile(path)` → `readSheets` → `readWorkers`. Zero código novo de leitura.

**Por que isso é seguro num APPX read-only?**
O diretório de instalação do APPX é somente-leitura, mas o exceljs apenas **lê** (`workbook.xlsx.readFile`). Nenhuma escrita acontece sobre o arquivo de exemplo.

---

## 12. PROCESSO PRINCIPAL — `src/main/index.ts`

```ts
const win = new BrowserWindow({
  width: 1024, height: 680,
  minWidth: 780, minHeight: 540,
  backgroundColor: '#0F1F4D',
  titleBarStyle: 'hidden',
  titleBarOverlay: {
    color: '#0C1840',
    symbolColor: '#8FB3F0',
    height: 40,
  },
  // ...
})
```

**Por que `titleBarStyle: 'hidden'`?**
Remove a barra de título padrão do Windows (cinza, genérica) e substitui pela `titleBarOverlay` — que mantém os botões nativos de minimizar/maximizar/fechar, mas permite customizar a cor de fundo. O resultado é uma barra de título integrada ao design dark navy do app.

**Por que `backgroundColor: '#0F1F4D'`?**
O Chromium renderiza um fundo branco por padrão durante o carregamento do HTML. Definir `backgroundColor` com a cor de fundo do app elimina o "flash branco" na inicialização.

**Por que `nativeTheme.themeSource = 'dark'`?**
Força o tema dark para todos os elementos nativos do Electron (menus contextuais, diálogos de arquivo). Sem isso, o `dialog.showOpenDialog()` apareceria com tema claro mesmo que o app seja dark.

---

## 13. ROTEAMENTO — `src/renderer/src/App.tsx`

O app não usa React Router — navegação por estado simples:

```ts
type Route = 'loading' | 'onboarding' | 'main' | 'settings'

useEffect(() => {
  window.api.config.get()
    .then((res) => {
      if (res.success && res.data) {
        setCompany(res.data)
        setRoute('main')
      } else {
        setRoute('onboarding')
      }
    })
    .catch(() => setRoute('onboarding'))
}, [])
```

**Por que não usar React Router?**
O app tem 3 telas. React Router adicionaria ~30 KB ao bundle, hash routing ou memory router, e configuração de BrowserWindow. Para um app desktop com 3 rotas simples, estado local é mais direto.

**Por que `.catch(() => setRoute('onboarding'))`?**
Se o IPC falhar por qualquer motivo (processo main travado, arquivo de config bloqueado), a promise rejeita. Sem o `.catch`, o spinner de loading ficaria preso para sempre. O fallback para onboarding permite ao usuário reconfigurar sem precisar fechar e reabrir o app.

---

## 14. TELA PRINCIPAL — `src/renderer/src/pages/Main.tsx`

### 14.1 — Máquina de estados

```ts
type Status = 'idle' | 'loading' | 'ready' | 'generating' | 'done' | 'error'
```

O status controla o que é exibido no painel esquerdo:
- `idle` → Dropzone (convite para selecionar arquivo)
- `loading` → Spinner + "Lendo planilha..."
- `ready` → Lista de funcionários + botão "Gerar Recibos"
- `generating` → Botão desabilitado + texto "Gerando..."
- `done` → Banner verde "PDF gerado com sucesso." + link "Abrir"
- `error` → Banner vermelho com a mensagem de erro

**Por que estado explícito em vez de múltiplos booleanos?**
Com booleanos (`isLoading`, `isGenerating`, `hasError`), estados impossíveis ficam possíveis: `isLoading && isGenerating` é inválido, mas o TypeScript não detectaria. Com um único `Status`, o compilador garante exclusividade.

### 14.2 — Preview paginado

```ts
const selectedWorkers = workers.filter((w) => selected.has(w.id))
const pageCount = Math.ceil(selectedWorkers.length / receiptsPerPage) || 0
const pageWorkers = selectedWorkers.slice(pageIndex * receiptsPerPage, (pageIndex + 1) * receiptsPerPage)
```

O preview mostra exatamente o que vai no PDF: se `receiptsPerPage = 2`, o componente `A4Page` exibe 2 recibos sobrepostos, lado a lado verticalmente, com as mesmas proporções do A4 real.

**Por que o cálculo `W * 1.4142`?**
A4 tem proporção √2 ≈ 1.4142. Com `W = 460px`, `H = Math.round(460 * 1.4142) = 651px`. O preview nunca vai distorcer a proporção do papel, independente da resolução da tela.

### 14.3 — Drag and drop

```ts
const handleDrop = useCallback((e: React.DragEvent) => {
  e.preventDefault()
  const file = e.dataTransfer.files[0]
  const path = file && (file as File & { path?: string }).path
  if (path) void loadFile(path)
}, [])
```

**Por que `(file as File & { path?: string }).path`?**
No browser padrão, o objeto `File` não tem propriedade `.path`. No Electron, o Chromium customizado adiciona `.path` com o caminho real no sistema de arquivos. O cast é necessário porque a tipagem do TypeScript para `File` segue o padrão web, não a extensão Electron.

### 14.4 — Recibos por folha

```ts
const [receiptsPerPage, setReceiptsPerPage] = useState(2)

useEffect(() => {
  setPageIndex(0)
}, [receiptsPerPage])
```

**Por que resetar `pageIndex` quando `receiptsPerPage` muda?**
Se estamos na página 3 com 2 recibos/folha (total: 10 recibos), ao mudar para 3 recibos/folha a paginação tem apenas 4 páginas. O índice 3 seria inválido. O `useEffect` garante reset automático.

### 14.5 — Seleção de data do recibo

A data do recibo é selecionável pelo usuário — por padrão é a data atual, mas pode ser qualquer data. O componente usa o `<input type="date">` nativo do Chromium, estilizado com CSS para corresponder ao design dark do app.

```ts
const [receiptDate, setReceiptDate] = useState<string>(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})
```

**Por que string ISO `YYYY-MM-DD` e não objeto `Date`?**
O `<input type="date">` trabalha com string no formato ISO. Converter para `Date` e de volta a ISO a cada render adicionaria operações desnecessárias. Ao enviar para o IPC, a string é convertida para `Date` uma única vez: `new Date(receiptDate)`.

**Por que o IPC tem tratamento especial para serialização de `Date`?**
O `contextBridge` do Electron serializa todos os valores como JSON. Objetos `Date` são convertidos para string ISO automaticamente. Em `generatePdf`, o lado main detecta isso:
```ts
const rawDate = (options as GeneratePdfOptions & { date?: unknown }).date
const date = rawDate instanceof Date ? rawDate : (rawDate ? new Date(rawDate as string) : new Date())
```

### 14.6 — Arquivos recentes

A tela inicial exibe os últimos 5 arquivos usados. Ao abrir o app, o `useEffect` carrega tanto a config da empresa quanto os recentes em paralelo:

```ts
useEffect(() => {
  Promise.all([
    window.api.config.get(),
    window.api.recent.get(),
    window.api.app.getVersion(),
  ]).then(([configRes, recentRes, versionRes]) => {
    if (configRes.success && configRes.data) { setCompany(configRes.data); setRoute('main') }
    else setRoute('onboarding')
    if (recentRes.success) setRecentFiles(recentRes.data)
    if (versionRes.success) setAppVersion(versionRes.data)
  }).catch(() => setRoute('onboarding'))
}, [])
```

Na tela principal (status `idle`), cada arquivo recente aparece como botão clicável. Clicar carrega o arquivo diretamente, sem precisar do dialog de seleção.

**Por que carregar versão aqui junto com config e recentes?**
É uma única round-trip de inicialização que ocorre uma vez. Carregar versão na abertura (em vez de apenas quando o modal Sobre é aberto) evita que o modal mostre "..." por um instante antes da versão aparecer.

### 14.7 — Modal Sobre

O modal Sobre exibe versão do app, descrição, declaração de privacidade e copyright. É aberto pelo botão `ⓘ` na barra de título.

```tsx
function AboutModal({ version, onClose }: { version: string; onClose: () => void }) {
  return (
    <div onClick={onClose}    // backdrop fecha ao clicar fora
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000 }}>
      <div onClick={(e) => e.stopPropagation()}  // clique interno não fecha
        style={{ ... }}>
        {/* ícone SVG, wordmark ReciboPro, versão, divider,
            descrição, declaração de privacidade, copyright, botão fechar */}
      </div>
    </div>
  )
}
```

**Por que `e.stopPropagation()` no div interno?**
Sem isso, clicar em qualquer parte do conteúdo do modal (incluindo o texto) propagaria o evento até o backdrop e fecharia o modal. O `stopPropagation` isola os cliques internos do backdrop.

**Por que o botão `ⓘ` usa `WebkitAppRegion: 'no-drag'`?**
A barra de título do app usa `WebkitAppRegion: 'drag'` para permitir arrastar a janela. Qualquer elemento dentro dela que precise ser clicável precisa sobrescrever para `'no-drag'` — caso contrário, o clique é interpretado como início de drag e o evento `onClick` nunca dispara.

### 14.8 — Carregar exemplo (testabilidade)

No estado `idle`, abaixo do Dropzone, há um botão secundário **"ou carregar exemplo"**:

```ts
async function loadSample() {
  const res = await window.api.excel.samplePath()
  if (!res.success || !res.data) return
  await loadFile(res.data)   // reaproveita o fluxo normal
}
```

Ele carrega a planilha embutida (`exemplo-recibopro.xlsx`: Carlos Silva R$500, Ana Lima R$950, Pedro Costa R$1200) sem o usuário precisar ter ou baixar nenhum arquivo.

De forma simétrica, o **Onboarding** ([§13](#13-roteamento--srcrendererrcappTsx)) tem o link **"Apenas testando? Carregar dados de exemplo"**, que semeia uma `CompanyConfig` demo e pula direto para a tela principal.

**Por que esses dois botões existem?**
Não são feature de produto — são requisito de **certificação**. Sem eles, um instalador novo (sem config salva e sem planilha) cai numa tela de cadastro que exige um CNPJ válido, intestável por quem não é brasileiro. Foi a causa raiz das reprovações 10.3.1 na Microsoft Store (ver §19). Com os dois botões, qualquer pessoa testa o app inteiro em 2 cliques, offline.

---

## 15. DESIGN SYSTEM — `src/renderer/src/styles/globals.css`

A V2 usa Tailwind CSS v4 com configuração CSS-first via `@theme`:

```css
@theme {
  --color-bg:               #080E28;
  --color-surface:          #0F1A3E;
  --color-surface-hover:    #152245;
  --color-surface-elevated: #1A2A52;
  --color-deep:             #05091A;

  --color-text:           #FFFFFF;
  --color-text-secondary: #8FB3F0;
  --color-text-muted:     #6B8FC2;

  --color-primary:  #2563EB;
  --color-accent:   #22C55E;
  --color-error:    #F87171;

  --font-sans: 'Inter Variable', 'Inter', system-ui, sans-serif;
}
```

**Por que Tailwind v4 e não v3?**
A v4 elimina o `tailwind.config.js` — o design system vive diretamente em CSS, dentro de `@theme {}`. Isso permite que as variáveis CSS (`--color-bg`, `--color-primary`, etc.) sejam usadas tanto pelas classes Tailwind (`bg-[--color-bg]`) quanto diretamente em `style={{}}` inline — único padrão de aplicação de estilos, sem duplicação.

**Por que usar `style={{}}` inline em vez de classes Tailwind em vários componentes?**
O Tailwind v4 + Vite tem um problema com valores arbitrários gerados dinamicamente (ex: `paddingTop: ${spacing}px`). O Vite não analisa valores computados em runtime — a classe não seria gerada no bundle de produção. Para valores que dependem de estado (`signatureSpacing`, dimensões calculadas), inline styles são obrigatórios.

**Por que `user-select: none` no body?**
Aplicações desktop não são documentos de texto. Clicar e arrastar em labels, botões ou rótulos não deve selecionar texto — comportamento padrão em apps nativos Windows. Reativado para `input` e `textarea` onde faz sentido.

**Por que `--color-text-muted: #6B8FC2` e não uma cor mais escura?**
Contraste mínimo WCAG AA: 4.5:1 para texto normal. O fundo `#080E28` + texto `#6B8FC2` = **5.2:1** — passa. A cor anterior `#4A6A9A` ficava em ~3.8:1 — reprovava acessibilidade.

---

## 16. GERAÇÃO DO EXECUTÁVEL WINDOWS — PASSO A PASSO

### 16.1 — Ferramentas de empacotamento avaliadas

| Ferramenta | Abordagem | Veredicto |
|---|---|---|
| **electron-builder** | Empacota Electron + gera instalador | **Escolhido** — suporte nativo a NSIS e MSIX |
| electron-forge | Alternativa oficial Electron | Menos configurável para NSIS avançado |
| manual | Copiar `dist/` + criar NSIS script | Complexo sem benefícios |

### 16.2 — Configuração do electron-builder

A configuração migrou de `electron-builder.config.ts` (TypeScript) para `electron-builder.yml` (YAML) — o formato padrão e mais estável do electron-builder, sem necessidade de compilação prévia. O `electron-builder.config.ts` legado foi **removido** do projeto: existiam dois configs divergentes (o `.ts` apontava para `identityName: HigherMind.ReciboPro` e `output: release`), e manter os dois era um footgun. Hoje existe apenas o `.yml`.

```yaml
# electron-builder.yml
appId: com.highermind.recibopro
productName: ReciboPro
directories:
  buildResources: resources
  output: dist
files:
  - out/**/*
# Planilha de exemplo empacotada (botão "carregar exemplo" — ver §11.4 e §14.8)
extraResources:
  - from: resources/sample/exemplo-recibopro.xlsx
    to: exemplo-recibopro.xlsx
win:
  icon: resources/icon.ico
  target:
    - target: nsis
      arch: x64
    - target: appx
      arch: x64
nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
appx:
  applicationId: ReciboPro
  identityName: CleitonEugenio.ReciboPro
  publisher: "CN=58749C1B-798E-462B-AA80-0FCB2D1DB879"
  publisherDisplayName: Cleiton Eugenio
  backgroundColor: "#1B4ECC"   # navy do tile do ícone (ver §20)
  languages: [pt-BR]
  showNameOnTiles: false
```

**Por que `extraResources` e não o glob `files`?**
O `files` do `.yml` inclui apenas `out/**/*` — `resources/` não entra no asar do app. `extraResources` copia o arquivo para `process.resourcesPath` no app empacotado, que é onde o handler `excel:sample-path` (§11.4) procura. É o mecanismo confiável para shipar um asset acessível em runtime.

**Por que `oneClick: false` e `allowToChangeInstallationDirectory: true`?**
Ao contrário de apps corporativas que assumem instalação silenciosa, o ReciboPro é distribuído para usuários não técnicos. Mostrar o diálogo de instalação com opção de pasta é mais transparente e evita surpresas.

**Por que o `publisher` do appx precisa ser exato?**
O campo `publisher` no MSIX deve ser **exatamente igual** ao Publisher CN da conta no Partner Center. O CN correto é obtido em: Partner Center → ReciboPro → Identidade do produto → Package/Identity/Publisher. Uma diferença de maiúscula, espaço ou ponto faz a validação do pacote falhar na Store.

**Status de publicação:**
O ReciboPro está publicado e live na Microsoft Store desde **15/06/2026** (a primeira submissão passou por várias reprovações de certificação até ser aprovada — ver §19). Store ID / Product ID: `9PG33DDBKDTC`. O `npm run dist:msix` gera tanto o `.exe` (NSIS) quanto o `.appx` (Store) em `dist/` (artefato atual: `ReciboPro-2.0.4-Setup.appx`).

### 16.3 — Processo de build

```
npm run dist:win
  → tsc --noEmit (verifica tipos)
  → electron-vite build (compila main + preload + renderer)
       main/index.ts  → out/main/index.js  (15 KB)
       preload/index.ts → out/preload/index.js (0.86 KB)
       renderer → out/renderer/ (CSS + JS + fontes woff2)
  → electron-builder --win  (lê electron-builder.yml)
       packager: copia Electron + out/ → dist/win-unpacked/
       rcedit: atualiza recursos do .exe (versão, copyright)
       NSIS: empacota dist/win-unpacked/ → dist/ReciboPro Setup 2.0.0.exe
```

**Por que dois `tsconfig`?**
- `tsconfig.node.json` — compila `src/main/` e `src/preload/` com `module: ESNext` + tipos Node.js
- `tsconfig.web.json` — compila `src/renderer/` e `src/shared/` com tipos DOM

O `tsconfig.json` raiz apenas referencia os dois. Isso evita que código do renderer importe `fs` (tipo Node.js disponível) e vice-versa.

### 16.4 — Estrutura de saída

```
out/          → compilado pelo electron-vite (ignorado no git)
dist/         → win-unpacked/ + recibo-pro Setup 2.0.0.exe
release/      → release/ (saída configurada no electron-builder)
```

O arquivo para distribuição é `dist/recibo-pro Setup 2.0.0.exe` (~87 MB). Pode ser copiado para qualquer computador Windows x64 e executado com dois cliques.

---

## 17. TESTES

Framework: **Vitest 3** — compatível com Vite, sem configuração extra.

```bash
npm test          # roda uma vez
npm run test:watch  # modo watch
```

### 17.1 — tests/utils.test.ts — 35 testes

#### applyTemplate — 19 testes

| Teste | O que verifica |
|---|---|
| Substitui `[nome]` | Placeholder básico |
| Substitui `[funcionario]` sem acento | Aliases do nome |
| Substitui `[funcionário]` com acento | Unicode no placeholder |
| `[total]` contém `R$ 500,00` e `quinhentos reais` | Formato BRL + extenso |
| `[valor]` igual a `[total]` | Alias de total |
| `[empresa]`, `[cnpj]`, `[cidade]` | Dados da empresa |
| `[endereco]` e `[endereço]` | Alias com/sem acento |
| `[endereco_completo]` com endereço preenchido | Inclui vírgula |
| `[endereco_completo]` com endereço vazio | String vazia |
| `[data]` formato pt-BR | "23 de abril de 2026" |
| Placeholders case-insensitive | `[NOME]`, `[Nome]` |
| Múltiplos placeholders no mesmo template | Integração |
| Mesmo placeholder repetido | Substituição global |
| Texto sem placeholders | Preservação |
| Template vazio | String vazia |
| Total com centavos | R$ 250,50 + extenso correto |

#### formatCNPJ — 9 testes

Cobre: 14 dígitos completo, input já formatado, 2 dígitos, 5 dígitos, 9 dígitos, 12 dígitos, 13 dígitos, excedente truncado, input vazio, input só com letras.

#### valorPorExtenso edge cases — 7 testes

| Teste | Resultado esperado |
|---|---|
| Valor negativo | `"R$ 0,00 (zero reais)"` |
| `-0.01` | `"R$ 0,00 (zero reais)"` |
| `1_000_000` | Contém "um milhão" e "R$ 1.000.000,00" |
| `2_000_000` | Contém "dois milhões" |
| `1_500_000` | Contém "um milhão" e "quinhentos mil" |
| `999_999_999` | Não explode (smoke test) |

### 17.2 — tests/excel.test.ts — 8 testes

Cria um arquivo `.xlsx` temporário no `beforeAll`, apaga no `afterAll`.

| Teste | O que verifica |
|---|---|
| `readSheets` retorna nomes das abas | ["Semana 1", "Semana 2"] |
| `readSheets` lança erro em arquivo inexistente | — |
| `readWorkers` lê funcionários com total > 0 | 2 funcionários |
| `readWorkers` ignora total zero | Filtro de Pedro Costa |
| `readWorkers` lê aba alternativa | Ana Lima na Semana 2 |
| `readWorkers` lança erro para aba inexistente | Mensagem inclui nome da aba |
| Filtra linhas cujo nome começa com "total" | Exclui "TOTAL GERAL" e "Total da semana" |
| Lê célula de fórmula corretamente | `{ formula: 'SUM(C2:J2)', result: 700 }` → 700 |

---

## 18. BUGS RESOLVIDOS — DETALHES TÉCNICOS

### Bug 1 — winCodeSign: erro de symlink no Windows sem Developer Mode

**Sintoma:**
```
ERROR: Cannot create symbolic link : O cliente não tem o privilégio necessário.
: darwin\10.12\lib\libcrypto.dylib
```
O build travava imediatamente após baixar `winCodeSign-2.6.0.7z`.

**Causa raiz:**
O `electron-builder` usa uma ferramenta chamada `winCodeSign` para:
1. Editar recursos do `.exe` via `rcedit` (versão, copyright, ícone)
2. Assinar o executável com `signtool.exe` (se houver certificado)

O `winCodeSign-2.6.0.7z` é um pacote multi-plataforma que contém binários para Windows, macOS e Linux. A versão para macOS inclui symlinks (`libcrypto.dylib` → `libcrypto.1.1.dylib`). O 7zip ao extrair no Windows tenta criar esses symlinks como links reais — o que exige o privilégio "Criar links simbólicos" do Windows, disponível apenas com Developer Mode ou conta de Administrador.

O `electron-builder` usa a ferramenta `app-builder` (binário Go pré-compilado) que por sua vez chama 7zip com o comando:
```
7za.exe x -snld -bd winCodeSign-2.6.0.7z -o{dir_temp}
```
O 7zip extrai os arquivos Windows com sucesso, mas falha nos dois symlinks macOS com exit code 2. O `app-builder` interpreta exit code != 0 como falha fatal e descarta a extração. Cada build tentava baixar novamente, criando novos diretórios com IDs aleatórios no cache.

**Análise:**
Investigando o código do `app-builder` (via `strings` no binário e análise do `binDownload.js` em `node_modules/app-builder-lib/out/`), descobriu-se que o `app-builder download-artifact --name winCodeSign` verifica se existe um diretório chamado **exatamente `winCodeSign-2.6.0`** no cache antes de baixar. Se o diretório existe com conteúdo, retorna o caminho imediatamente (exit code 0).

**Fix aplicado:**
```bash
# Copiar conteúdo de uma extração parcial anterior (que tinha os binários Windows intactos)
# para o diretório com o nome exato que o app-builder espera
cp -r "$LOCALAPPDATA/electron-builder/Cache/winCodeSign/029620843" \
      "$LOCALAPPDATA/electron-builder/Cache/winCodeSign/winCodeSign-2.6.0"
```
Verificação:
```bash
SZA_PATH="7za.exe" ELECTRON_BUILDER_CACHE="..." \
  app-builder.exe download-artifact --name winCodeSign
# Saída: C:\...\Cache\winCodeSign\winCodeSign-2.6.0
# Exit code: 0
```

O fix é permanente — o diretório persiste no cache entre builds. Na próxima execução de `npm run dist:win`, o `app-builder` encontra `winCodeSign-2.6.0` e não tenta baixar novamente.

**Alternativa para máquinas novas:**
Ativar o Modo de Desenvolvedor do Windows: Configurações → Sistema → Para Desenvolvedores → Modo de Desenvolvedor (ativo). Isso concede o privilégio de criar symlinks.

---

### Bug 2 — Teste formatCNPJ: expectativa errada para 9 dígitos

**Sintoma:**
```
AssertionError: expected '12.345.678/9' to equal '12.345.678.9'
```

**Causa raiz:**
O teste foi escrito esperando que o separador entre o bloco de 8 dígitos e os 4 da filial fosse um ponto (`.`). O formato real do CNPJ é `XX.XXX.XXX/XXXX-XX` — a barra (`/`) aparece após o 8º dígito, não um ponto.

Com 9 dígitos (`123456789`), a função retorna `12.345.678/9` — correto pelo padrão CNPJ. O teste estava errado, não a função.

**Fix:** Corrigir a expectativa do teste para `'12.345.678/9'`.

---

### Bug 3 — extenso.ts: barrel file deletado mas ainda importado pelo teste

**Sintoma:**
```
Error: Cannot find module '../src/main/services/extenso'
```

**Causa raiz:**
Existia um arquivo `src/main/services/extenso.ts` que era um barrel re-exportando `valorPorExtenso` de `src/shared/utils.ts`. Durante a reorganização do código, o arquivo foi deletado (correto — era redundante). Porém, o arquivo de testes `tests/extenso.test.ts` ainda importava de `'../src/main/services/extenso'`.

**Fix:** Atualizar o import no arquivo de teste para apontar diretamente para `'../src/shared/utils'`.

---

### Bug 4 — App.tsx: spinner infinito em caso de falha de IPC

**Sintoma:**
Em máquinas onde o processo main travava durante a inicialização, o app ficava preso na tela de loading (spinner) indefinidamente.

**Causa raiz:**
```ts
// Versão com bug
window.api.config.get().then((res) => {
  if (res.success && res.data) setRoute('main')
  else setRoute('onboarding')
})
// Sem .catch() — rejeição = spinner eterno
```

**Fix:**
```ts
window.api.config.get()
  .then((res) => {
    if (res.success && res.data) { setCompany(res.data); setRoute('main') }
    else setRoute('onboarding')
  })
  .catch(() => setRoute('onboarding'))
```
Em qualquer falha de IPC, o app redireciona para o Onboarding onde o usuário pode reconfigurar.

---

### Bug 5 — exceljs: CellFormulaValue não é um número simples

**Sintoma:**
Funcionários com a coluna TOTAL calculada por fórmula apareciam com total `NaN` ou `0`.

**Causa raiz:**
Planilhas criadas com fórmulas armazenam o valor da célula como `CellFormulaValue`:
```ts
// O que a célula contém na planilha real:
{ formula: 'SUM(C2:J2)', result: 700 }

// O que o código tentava fazer originalmente:
const total = Number(row.getCell(11).value) // → NaN (não é number nem string)
```

**Fix:** A função `cellNumber()` trata explicitamente o caso `'result' in val`:
```ts
if (val !== null && typeof val === 'object' && 'result' in val) {
  const r = (val as { result: unknown }).result
  return typeof r === 'number' ? r : Number(r)
}
```

---

### Bug 6 — Tailwind v4: classes arbitrárias com valores dinâmicos não geradas

**Sintoma:**
Valores como `paddingTop: ${spacing * 0.77}px` ou dimensões calculadas não funcionavam como classes Tailwind arbitrárias (`pt-[${...}]`).

**Causa raiz:**
O Tailwind v4 analisa o código estaticamente para gerar o CSS. Valores calculados em runtime (`${company.signatureSpacing ?? 44 * 0.77}`) não existem em tempo de análise — a classe correspondente nunca seria incluída no bundle de produção.

**Fix:** Usar inline styles para todos os valores que dependem de estado ou cálculo dinâmico:
```tsx
// ❌ Não funciona em produção com valores dinâmicos
<div className={`pt-[${spacing * 0.77}px]`}>

// ✅ Correto
<div style={{ paddingTop: `${spacing * 0.77}px` }}>
```

### Bug 7 — `file.path` removido no Electron 32 quebra drag and drop silenciosamente

**Sintoma:** Arrastar um arquivo `.xlsx` para o app não fazia nada. Nenhum erro no console, nenhuma mensagem para o usuário — o arquivo simplesmente não carregava.

**Causa:** O código usava `(file as File & { path?: string }).path` para obter o caminho do arquivo arrastado. Essa propriedade `.path` era uma extensão do Electron no objeto `File` do DOM. A partir do **Electron 32**, com `contextIsolation: true`, ela foi removida do renderer e passa a retornar `undefined` silenciosamente.

```ts
// ❌ Electron 31 e anterior — funcionava
const path = (file as File & { path?: string }).path  // undefined no Electron 32+

// ❌ Nenhum erro, nenhum aviso — simplesmente retornava null
if (path) void loadFile(path)  // nunca executava
```

**Por que é difícil de diagnosticar?** A ausência de erro é a parte traiçoeira. `file.path` retorna `undefined` sem lançar exceção, então o `if (path)` simplesmente não executava. O drag and drop "não funcionava" sem qualquer pista do motivo.

**Fix:** Usar `webUtils.getPathForFile(file)`, a API oficial do Electron 32+ para obter o caminho de arquivos arrastados. O método é importado no preload e exposto via `contextBridge`:

```ts
// src/preload/index.ts
import { contextBridge, ipcRenderer, webUtils } from 'electron'

const api = {
  // ...
  getPathForFile: (file: File): string => webUtils.getPathForFile(file),
}
```

```ts
// src/renderer/src/pages/Main.tsx
const extractPath = useCallback((e: React.DragEvent): string | null => {
  e.preventDefault()
  e.stopPropagation()
  const file = e.dataTransfer.files[0]
  if (!file) return null
  return window.api.getPathForFile(file)  // ✅ correto para Electron 32+
}, [])
```

**Lição:** Ao atualizar a versão do Electron, verificar o changelog de breaking changes em APIs do renderer — especialmente as que dependem de extensões do Node.js no contexto do browser (`file.path`, `process`, etc.). Com `contextIsolation: true`, o renderer é progressivamente mais isolado a cada versão major.

### Bug 8 — uuid < 14.0.0: vulnerabilidade CVE GHSA-w5hq-g745-h8pq

**Sintoma:**
`npm audit` reportava uma vulnerabilidade HIGH no pacote `uuid`:
```
uuid  <14.0.0
Severity: HIGH
uuid is vulnerable to Cross-Site Request Forgery (CSRF)
fix available via: npm audit fix --force
```

**Causa raiz:**
O `exceljs` usa `uuid` como dependência transitiva (não direta). A versão instalada era `uuid@8.x`, que tem a vulnerabilidade. O `uuid` não é um runtime-only dep — qualquer versão vulnerável incluída no bundle representa risco.

**Fix:**
Adicionar `overrides` no `package.json` para forçar a versão correta **sem quebrar o exceljs**:
```json
"overrides": {
  "uuid": "^14.0.0"
}
```

**Por que `overrides` e não atualizar o exceljs diretamente?**
O `exceljs` não depende de `uuid` como peerDependency — é uma dep interna. A única forma de forçar uma versão transitiva específica sem fork do exceljs é via `overrides` (npm) ou `resolutions` (yarn). O `overrides` do npm é a solução oficial para esse cenário.

**Por que `^14.0.0` e não `^9.0.0` ou `^10.0.0`?**
O advisory especifica `uuid <14.0.0` como vulnerável. A versão `14.0.0` foi a primeira a corrigir a vulnerabilidade. Usar `^10.0.0` ou `^13.x` ainda estaria na faixa vulnerável.

**Nota sobre as 12 vulnerabilidades restantes:**
`npm audit` ainda reporta 12 vulnerabilidades moderadas, todas em `tar` via `electron-builder`. São dependências de **build time** — não são empacotadas no instalador final e não afetam o usuário. Podem ser ignoradas.

---

### Bug 9 — Última folha da prévia estica os recibos quando incompleta

**Sintoma:** Com 3 recibos por folha, a última folha tinha apenas 2 recibos. Na prévia, esses 2 recibos se esticavam para ocupar toda a altura da folha A4. O PDF gerado estava correto (dois recibos com espaço vazio abaixo), mas a prévia divergia da realidade.

**Causa:** O componente `A4Page` usava `display: flex; flex-direction: column` e renderizava os recibos diretamente como filhos. O CSS flex distribui o espaço disponível entre os filhos presentes — com 2 filhos numa página de 3, cada um recebia 50% da altura em vez de 33%.

```tsx
// ❌ Flex dividia o espaço entre os recibos presentes
<div style={{ display: 'flex', flexDirection: 'column', gap: '8px', height: '651px' }}>
  <ReceiptPreview worker={w1} />  {/* crescia para 50% */}
  <ReceiptPreview worker={w2} />  {/* crescia para 50% */}
  {/* terceiro slot inexistente */}
</div>
```

**Fix:** `A4Page` passou a calcular a altura de cada slot com base em `count` (total de recibos por folha) e sempre renderiza exatamente `count` slots de altura fixa — os vazios ficam como `<div>` em branco:

```tsx
const slotH = Math.floor((H - PAD_V * 2 - GAP * (count - 1)) / count)

{Array.from({ length: count }, (_, i) => (
  <div key={i} style={{ height: `${slotH}px`, flexShrink: 0, overflow: 'hidden' }}>
    {workers[i] && <ReceiptPreview worker={workers[i]} ... />}
  </div>
))}
```

**Lição:** Sempre que um componente de layout precisa representar uma grade com slots fixos (como folhas de impressão), os slots devem ter dimensão explícita e existir independente do conteúdo — nunca delegar ao flex para distribuir espaço dinamicamente.

---

### Bug 10 — cellNumber: valores de moeda armazenados como texto não eram lidos

**Sintoma:** O ReciboPro não conseguia ler a planilha do usuário. A coluna TOTAL tinha valores formatados como texto de moeda (`"R$ 500,00"`, `"R$ 1.200,00"`) em vez de números. `Number("R$ 500,00")` retorna `NaN`, então o filtro `!isNaN(total) && total > 0` excluía todos os funcionários — a lista ficava vazia.

**Causa:** A função `cellNumber()` só tratava o caso `typeof val === 'number'` e fórmulas. Strings eram passadas direto para `Number()`, que não sabe interpretar o formato BRL.

**Fix:** Adicionada a função `parseCurrencyString()` que limpa o prefixo de moeda e converte o formato BRL (vírgula como decimal) para float:

```ts
function parseCurrencyString(s: string): number {
  const cleaned = s.replace(/[^\d.,]/g, '')
  if (!cleaned) return NaN
  if (cleaned.includes(',')) return Number(cleaned.replace(/\./g, '').replace(',', '.'))
  const dotCount = (cleaned.match(/\./g) ?? []).length
  if (dotCount > 1) return Number(cleaned.replace(/\./g, ''))
  return Number(cleaned)
}
```

**Formatos suportados:** `"R$ 600,00"` → `600`, `"R$ 1.200,00"` → `1200`, `"R$ 1.234,56"` → `1234.56`, `"500"` → `500`.

---

### Bug 11 — electron-builder.yml: campo `assets` inválido na seção `appx`

**Sintoma:** `npm run dist:win` falhava com erro de validação de schema:
```
configuration.appx has an unknown property 'assets'
```

**Causa:** A configuração tinha `assets: resources/appx-assets` na seção `appx`, mas esse campo não existe na API do electron-builder 25.x. Era um campo documentado em versões anteriores que foi removido.

**Fix:** Removida a linha `assets: resources/appx-assets` do `electron-builder.yml`. O electron-builder usa os ícones do pacote APPX diretamente do campo `win.icon`.

---

### Bug 12 — Onboarding obrigatório tornava o app intestável para a Microsoft

**Sintoma:** Reprovação repetida (5×) na certificação com a política 10.3.1 "App Is Testable — Test Account": *"we can't test the product because its primary functionality requires a test account, but no test credentials were provided."* — apesar do app **não ter login algum**.

**Causa:** Numa VM de certificação limpa, sem `company.json` salvo, o `App.tsx` roteia direto para o Onboarding, que exige **Nome + CNPJ válido (≥18 dígitos, documento fiscal brasileiro) + Cidade**, com o botão "Continuar" desabilitado até `isValid`. Um testador estrangeiro não tem como inventar um CNPJ válido nem possui uma planilha `.xlsx` — empacava na primeira tela e arquivava o template de "requires account".

**Fix:** Dois caminhos de exemplo embutidos (§14.8): link "Carregar dados de exemplo" no Onboarding (semeia `CompanyConfig` demo) + botão "carregar exemplo" no Main (lê a planilha empacotada via `excel:sample-path`). O app passa a ser testável em 2 cliques, offline, sem digitar nem baixar nada.

---

### Bug 13 — Ícone ilegível em tamanho pequeno (ilustração detalhada encolhida)

**Sintoma:** O ícone na barra de tarefas aparecia como um borrão indistinguível.

**Causa:** O `icon.ico` e o `Square44x44Logo` usavam a **ilustração detalhada** (`icon_nobg_1024.png` — documento com texto "recibopro", linhas finas, "ASSINATURA"). Essa arte é linda em 150-256px, mas vira ruído ilegível em 16-48px.

**Fix:** Estratégia de dois tamanhos no `generate_appx_assets.py` (§20): **≥64px** usa a ilustração completa sobre o tile azul; **<64px** desenha uma versão simplificada vetorial (tile azul + documento branco + header verde + seta verde). Um segundo bug embutido neste: a primeira tentativa usava `Image.thumbnail()`, que **só reduz** — como a ilustração (987px) é menor que o alvo em alta resolução, ela ficava minúscula no centro; corrigido com um `fit()` que escala para cima e para baixo mantendo proporção.

---

## 19. CERTIFICAÇÃO E PUBLICAÇÃO NA MICROSOFT STORE

Publicar o ReciboPro não foi um passo único. Foram mais de seis submissões, cada reprovação por uma política diferente. Esta seção documenta cada bloqueio e sua resolução — porque a mensagem literal da Microsoft raramente apontava a causa real.

### 19.1 — Política 10.1.1.11 "On Device Tiles"

**Reprovou porque:** o electron-builder, sem assets customizados, usava os tiles `SampleAppx.*.png` padrão — a Microsoft reconhece essas imagens de exemplo e reprova.

**Resolvido com:** tiles APPX próprios em `resources/appx/` (`StoreLogo`, `Square44x44Logo`, `Square150x150Logo`, `Wide310x150Logo`), gerados pelo `generate_appx_assets.py`. O electron-builder procura custom tiles em `resources/appx/` (constante `APPX_ASSETS_DIR_NAME = "appx"`).

### 19.2 — Política 10.3.1 "App Is Testable" (a mais difícil — 5 reprovações)

A mensagem dizia que o app "exigia uma conta de teste", mas o ReciboPro **não tem login**. A causa real era o Onboarding obrigatório com CNPJ válido somado à ausência de qualquer planilha para testar (a única estava hospedada no Google Drive, que numa VM de certificação pede login Google ou é bloqueado por rede). Detalhe técnico completo no **Bug 12**. Resolução: botões de dados de exemplo embutidos (§14.8) + notas de certificação reescritas, sem dependência externa.

> **Lição:** quando a política reclama de "test account" num app sem login, o problema quase sempre é que o testador **não consegue chegar à função principal** — formulário obrigatório, dado externo inacessível, ou crash. A mensagem é um template; a causa é o caminho até a primeira ação útil.

### 19.3 — Política 10.1.3 "Search Terms"

**Reprovou porque:** uma das palavras-chave da listagem era **"planilha excel"** — "Excel" é título de produto de terceiro, proibido como termo de descoberta.

**Resolvido com:** remoção do termo (apenas metadados da listagem, sem rebuild). As demais palavras-chave (recibo, recibo PDF, pagamento, prestação de serviço, rh, gerador de recibos) são genéricas e permitidas.

### 19.4 — Privacidade (Política 7.19 / 10.5.1)

Houve confusão inicial achando que a URL de política de privacidade era obrigatória. O Partner Center **aceita texto inline** como alternativa à URL para apps Win32/Desktop Bridge — o texto inline preenchido é válido.

### 19.5 — Publicação e atualizações

- **15/06/2026:** primeira versão aprovada e live na Store (gratuita, categoria Produtividade, publisher Cleiton Eugenio).
- **Regra de versão:** cada pacote reenviado com conteúdo diferente exige **bump de versão** (`package.json`), pois o full name `CleitonEugenio.ReciboPro_X.X.X.0_X64` precisa ser único. Daí a sequência 2.0.0 → 2.0.1 → … → 2.0.4.
- **Atualizar o app:** Partner Center → ReciboPro → "Iniciar atualização" (clona a submissão anterior) → módulo **Pacotes** (subir o novo `.appx`; o antigo é removido automaticamente ao salvar — não remover manualmente) → **Enviar para a Store**. Os checkboxes "atualização gradual" e "obrigatória" ficam desmarcados.

---

## 20. SISTEMA DE ÍCONES — `resources/generate_appx_assets.py`

### 20.1 — O problema central

Um ícone não é uma imagem única. O Windows o renderiza de 16px (lista/barra de tarefas) a 256px+ (Start tile, Store). A ilustração da marca (`icon_nobg_1024.png`: documento + header verde "recibopro" + planilha azul atrás + círculo verde com seta) é excelente em tamanhos grandes e **ilegível** em pequenos (ver Bug 13).

### 20.2 — A fonte da verdade: o design system

O arquivo `recibopro - Design System.html` define a identidade. O ícone oficial (`makeIconD`) é um **tile azul gradiente** (`#2563EB → #1B4ECC`, a cor primária "azul confiança"), com o verde `#22C55E` apenas como **accent** (aprovação). Regra explícita: *"wordmark omitido abaixo de 64×64px"*.

> Uma primeira tentativa fez o ícone como um tile **verde** — estava off-brand: verde é accent, não primary. Corrigido para azul após conferência com o design system.

### 20.3 — Estratégia de dois tamanhos

O `generate_appx_assets.py` (PIL, supersampling 8× para anti-aliasing) gera tudo a partir da marca:

| Faixa | Renderização |
|---|---|
| **≥ 64px** | Tile azul gradiente + ilustração completa (`icon_nobg_1024.png`) composta sobre ele, escalada por um `fit()` que mantém proporção |
| **< 64px** | Versão simplificada vetorial: tile azul + documento branco + header verde + 3 linhas + círculo verde com seta |

### 20.4 — Assets gerados

- **Tiles APPX** (full-bleed, o Windows arredonda): `StoreLogo` 50×50, `Square44x44Logo` 44×44, `Square150x150Logo` 150×150, `Wide310x150Logo` 310×150.
- **`icon.ico`** multi-tamanho (16/24/32/48/64/128/256, cantos arredondados com transparência) — para o `.exe`, NSIS e janela em dev.
- **`icon.png`** 512 (master arredondado).
- **`backgroundColor: "#1B4ECC"`** no `electron-builder.yml` — navy do tile, para coesão do plating do APPX.

### 20.5 — Logos da listagem da Store

A listagem da Store usa imagens separadas dos tiles do pacote, nos tamanhos **300×300, 150×150 e 71×71**. Como o pacote só tem 44/50/150/310, a Store escalava/inventava os demais (resultado inconsistente). Solução: gerar os três dedicados (`store-logo-300/150/71.png`, full-bleed azul) e subir nos slots correspondentes em Listagens da Store → Imagens de exibição. Regra: substituir os três ou nenhum, nunca misturar com extração automática do pacote.

---

## 21. PRÓXIMOS PASSOS PREVISTOS

O app está publicado na Microsoft Store (Store ID: `9PG33DDBKDTC`) e funcional. As melhorias abaixo são evoluções identificadas:

- **✅ Publicação na Microsoft Store:** Live desde 15/06/2026 após o ciclo de certificação descrito na §19. Conta de desenvolvedor gratuita (programa Windows).
- **✅ Ícone redesenhado:** Marca azul do design system, legível em todos os tamanhos (§20).
- **Período da semana no recibo:** Adicionar placeholder `[periodo]` que lê o nome da aba (`"Semana 04-09/04"`) e extrai o intervalo de datas
- **CPF no recibo:** Adicionar coluna opcional de CPF na planilha, incluir no recibo via placeholder `[cpf]`
- **Autoupdate:** Configurar `electron-updater` para atualizações automáticas via GitHub Releases
- **Assinatura digital:** Adquirir certificado de assinatura de código EV para eliminar o aviso "Editor desconhecido" do Windows Defender SmartScreen

---

## 22. COMO USAR O PROGRAMA

### Primeira execução — Onboarding
1. Instale pela Microsoft Store (ou execute o `.exe` NSIS) — instala sem janela de assistente
2. Abra o app. Como não há configuração salva, o Onboarding abre automaticamente
3. Preencha nome da empresa, CNPJ (formatado automaticamente), endereço e cidade
4. Clique em "Salvar" — vai para a tela principal
   - **Apenas testando?** Clique em "Carregar dados de exemplo" para pular o cadastro com uma empresa demo

### Uso recorrente — Tela Principal
1. Clique em "Selecionar planilha" ou arraste o arquivo `.xlsx` para a área de drop
   - Ou clique em um dos **arquivos recentes** que aparecem na tela inicial (últimos 5)
   - Ou clique em "**carregar exemplo**" para abrir a planilha de demonstração embutida
2. Se a planilha tiver múltiplas abas, selecione a semana no dropdown
3. Selecione a **data do recibo** no campo de data (padrão: data de hoje)
4. A lista de funcionários aparece — todos selecionados por padrão
   - Use o campo de **busca** para filtrar funcionários por nome
5. O preview à direita mostra como ficará no PDF, página por página
6. Ajuste "Recibos por folha" no footer do preview (padrão: 2)
7. Clique em "Gerar Recibos" → escolha onde salvar → PDF criado
8. Clique "Abrir" no banner verde para abrir o PDF gerado

### Configurações da empresa — Aba "Empresa"
1. Clique na aba "Empresa" na barra de tabs
2. Edite nome, CNPJ, cidade, endereço
3. Use os toggles para mostrar/ocultar elementos do cabeçalho (nome, CNPJ, endereço)
4. Edite o título do recibo (padrão: "RECIBO DE PRESTAÇÃO DE SERVIÇO")
5. Ative **Valor em destaque** para exibir caixa cinza com o valor numérico em bold
6. Ajuste o modelo do recibo usando os placeholders disponíveis
7. Ajuste o espaçamento da assinatura com o slider
8. O preview ao vivo à direita atualiza conforme você edita
9. Clique "Salvar" — volta para a tela principal com as novas configurações

### Modal Sobre
- Clique no botão `ⓘ` na barra de título para abrir o modal Sobre
- Exibe versão do app, descrição, declaração de privacidade e copyright
- Clique fora do modal ou no botão "Fechar" para dispensar

### Placeholders disponíveis no modelo

| Placeholder | O que substitui |
|---|---|
| `[nome]` ou `[funcionario]` | Nome do funcionário |
| `[total]` ou `[valor]` | Valor em R$ + por extenso |
| `[empresa]` | Nome da empresa |
| `[cnpj]` | CNPJ formatado |
| `[cidade]` | Cidade |
| `[endereco]` | Endereço |
| `[endereco_completo]` | `, Endereço` (com vírgula, ou vazio) |
| `[data]` | Data de geração no formato pt-BR |

---

*Fim da documentação. Versão 2.0.4 — HigherMind. Atualizado em 17/06/2026 (publicação na Microsoft Store, sistema de ícones, dados de exemplo para certificação).*
