# ReciboPro V2 — Architecture

## Stack

| Layer | Technology | Why |
|---|---|---|
| Shell | **Electron 34** | Chromium bundled = renderização consistente no Windows. Suporte a MSIX via electron-builder. |
| Build | **electron-vite 3** | Vite para renderer (HMR rápido) + bundling correto de main/preload/renderer sem configuração manual. |
| UI | **React 19 + TypeScript strict** | Component model correto para estado local complexo. Strict mode captura bugs em dev. |
| Estilo | **CSS custom properties** | Design tokens centralizados. Sem framework extra. Dark-first. |
| PDF | **pdf-lib** | Geração programática de PDF no processo Node.js (main). Sem dependência de Python. |
| Excel | **exceljs** | Leitura de `.xlsx` ativa e mantida. UUID fixado em `^14.0.0` via overrides. |
| Config | **fs/promises + userData** | `app.getPath('userData')` é o local correto para dados de usuário no Windows. Zero dependências. |
| Testes | **vitest** | Mesmo runtime do Vite. Rápido, zero config, suporte a ESM nativo. |
| Packaging | **electron-builder** | NSIS (installer) + MSIX (Microsoft Store) em um comando. |

## Por que sem Python backend

A lógica da V1 foi portada para Node.js:
- Leitura de xlsx: `exceljs`
- Geração de PDF: `pdf-lib`
- Número por extenso: implementação própria em `src/shared/utils.ts`

Manter Python implicaria dois runtimes (+60 MB), subprocess IPC, dois processos, duas linguagens — sem ganho real para esta lógica.

---

## Estrutura de processos Electron

```
Main Process (Node.js)
  ├── ipc/handlers.ts         — handlers IPC com validação de input
  ├── services/
  │   ├── excel.ts            — leitura de planilha
  │   └── pdf.ts              — geração de recibos PDF (layout, wrap, highlight)
  └── store.ts                — persistência de config (company.json) e recentes (recent.json)

Preload (contextBridge)
  └── index.ts                — expõe window.api tipado; zero lógica de negócio

Renderer (React)
  ├── App.tsx                 — state machine: loading → onboarding | main | settings
  ├── pages/
  │   ├── Main.tsx            — fluxo principal: arquivo → aba → funcionários → PDF + modal Sobre
  │   ├── Onboarding.tsx      — configuração inicial da empresa
  │   └── Settings.tsx        — edição de config com prévia A4 ao vivo
  └── components/
      ├── WorkerList.tsx      — lista de funcionários com busca e checkboxes
      └── ReceiptPreview.tsx  — recibo em HTML (espelha o PDF)

Shared
  ├── types.ts                — interfaces Worker, CompanyConfig, GeneratePdfOptions, IpcResponse
  └── utils.ts                — valorPorExtenso, formatarData, applyTemplate, DEFAULT_TEMPLATE
```

---

## IPC API (`window.api`)

| Namespace | Método | Descrição |
|---|---|---|
| `config` | `get()` | Lê CompanyConfig do userData |
| `config` | `set(config)` | Persiste CompanyConfig |
| `recent` | `get()` | Retorna últimos 5 caminhos de arquivo |
| `recent` | `add(path)` | Adiciona caminho à lista de recentes |
| `excel` | `readSheets(path)` | Lista abas do xlsx |
| `excel` | `readWorkers(path, sheet)` | Lê funcionários da aba |
| `pdf` | `generate(options)` | Gera o PDF em disco |
| `dialog` | `openXlsx()` | Dialog de seleção de xlsx |
| `dialog` | `savePdf(name)` | Dialog de salvamento de PDF |
| `shell` | `openPath(path)` | Abre arquivo/pasta no Explorer |
| `app` | `getVersion()` | Versão do app (para modal Sobre) |
| — | `getPathForFile(file)` | `webUtils.getPathForFile` para drag & drop |

---

## CompanyConfig

```ts
interface CompanyConfig {
  name: string              // nome da empresa
  cnpj: string              // CNPJ formatado
  address: string           // endereço
  city: string              // cidade / UF
  headerShowName?: boolean  // exibe nome no cabeçalho do recibo (default: true)
  headerShowCnpj?: boolean  // exibe CNPJ no cabeçalho (default: true)
  headerShowAddress?: boolean // exibe endereço no cabeçalho (default: true)
  receiptTitle?: string     // título do recibo (default: 'RECIBO DE PRESTAÇÃO DE SERVIÇO')
  receiptTemplate?: string  // template do corpo (default: DEFAULT_TEMPLATE)
  signatureSpacing?: number // espaço antes da assinatura em pontos (default: 44)
  highlightValue?: boolean  // exibe valor em caixa destacada com bold (default: false)
}
```

---

## Template de recibo

`DEFAULT_TEMPLATE` em `src/shared/utils.ts` define o texto padrão. A função `applyTemplate()` substitui placeholders:

| Placeholder | Valor substituído |
|---|---|
| `[nome]` / `[funcionario]` | `worker.name` |
| `[total]` / `[valor]` | `valorPorExtenso(worker.total)` |
| `[empresa]` | `company.name` |
| `[cnpj]` | `company.cnpj` |
| `[cidade]` | `company.city` |
| `[endereco]` | `company.address` |
| `[data]` | `formatarData(date)` |

---

## Geração de PDF (`pdf.ts`)

O PDF é gerado com `pdf-lib` no processo main. Coordenadas em pontos, A4 (595.28 × 841.89 pt).

**Funções principais:**
- `receiptHeight(n)` — calcula altura disponível por recibo dado N recibos por página
- `wrapText()` — quebra string em linhas respeitando `maxWidth`
- `drawWrapped()` — desenha texto com wrap
- `drawBodyHighlighted()` — word-wrap consciente de cor: tokeniza palavras como `isValue` ou não, constrói linhas, desenha cada palavra com sua fonte (bold/regular) e cor (BLACK) individualmente
- `drawReceipt()` — desenha um recibo completo: cabeçalho, divisor, caixa de valor (se `highlightValue`), corpo, data, linha de assinatura, nome

**Caixa de valor em destaque:**
Quando `company.highlightValue = true`, renderiza uma caixa cinza clara com label "VALOR" e o valor bold à direita. O texto por extenso no corpo fica em bold.

---

## Persistência

| Arquivo | Local | Conteúdo |
|---|---|---|
| `company.json` | `userData/company.json` | `CompanyConfig` serializado |
| `recent.json` | `userData/recent.json` | Array de strings (paths), máx. 5 |

---

## Prévia em tempo real (Settings)

`Settings.tsx` renderiza um `PreviewA4` com dimensões fixas (W=460, H=651) usando slots de altura fixa — idêntico ao cálculo do `A4Page` em `Main.tsx`. Isso garante paridade visual entre a prévia das configurações e a prévia principal.

---

## Segurança

- `contextIsolation: true` — renderer sem acesso ao Node.js
- `nodeIntegration: false` — sem `require()` no renderer
- `webSecurity: true` — CSP ativo
- Todos os inputs IPC validados com type guards antes de processar
- Nenhum dado coletado ou transmitido — processamento 100% local
- `uuid` (dep. runtime via exceljs) fixado em `>=14.0.0` via `overrides` (CVE GHSA-w5hq-g745-h8pq)

---

## Distribuição

```bash
npm run dist:msix   # MSIX para Microsoft Store
npm run dist:win    # MSIX + instalador NSIS
npm run pack        # pasta não empacotada (teste)
```

Configuração em `electron-builder.yml`. Veja [STORE_SETUP.md](STORE_SETUP.md) para publicação na Microsoft Store.

---

## Testes

```bash
npm run test
```

**58 testes, 3 suítes:**

| Suíte | Arquivo | O que testa |
|---|---|---|
| `utils.test.ts` | 35 testes | `valorPorExtenso`, `formatarData`, `applyTemplate`, DEFAULT_TEMPLATE, placeholders |
| `extenso.test.ts` | 14 testes | Conversão de valores para português (centavos, milhões, edge cases) |
| `excel.test.ts` | 9 testes | Leitura de planilha, múltiplas abas, células com fórmula/rich text |

---

## Fluxo principal

```
1. Primeira abertura → Onboarding (configura empresa uma vez)
2. Usos seguintes:
   a. Tela principal — dropzone ou arquivo recente
   b. Seleciona aba (semana), se houver mais de uma
   c. Escolhe data do recibo
   d. Filtra/desmarca funcionários por nome ou checkbox
   e. Ajusta recibos por folha e navega pela prévia
   f. "Gerar Recibos" → dialog de save → abre o PDF
```

---

## Custo operacional

Zero. Sem chamadas a APIs externas. Tudo roda localmente.
