# ReciboPro

Gerador de recibos de prestação de serviço para Windows. Lê uma planilha Excel, gera PDFs prontos para impressão com recibos personalizados por funcionário.

---

## Funcionalidades

- **Importação de planilha** — arraste ou selecione um `.xlsx`; planilhas com múltiplas abas têm seletor de semana
- **Lista de funcionários** — checkboxes individuais, seleção por visíveis, busca por nome em tempo real
- **Prévia A4 em tempo real** — visualize exatamente como o PDF vai ficar antes de gerar, com navegação por página
- **Data do recibo** — selecionável na interface; nome do PDF inclui mês e ano automaticamente
- **Arquivos recentes** — últimos 5 arquivos usados aparecem na tela inicial com um clique para reabrir
- **Recibos por folha** — 1 ou mais recibos por página A4, configurável na prévia
- **Modelo de texto editável** — corpo do recibo personalizável com placeholders (`[nome]`, `[total]`, `[empresa]`, etc.)
- **Valor em destaque** — opção para exibir o valor em uma caixa destacada no recibo (PDF e prévia)
- **Configuração da empresa** — nome, CNPJ, endereço, cidade, título do recibo, espaço de assinatura
- **Cabeçalho configurável** — ative/desative nome, CNPJ e endereço no cabeçalho individualmente
- **Modal Sobre** — versão do app, declaração de privacidade

---

## Estrutura da planilha

| Coluna | Índice | Conteúdo |
|--------|--------|----------|
| # | 0 | Número do funcionário |
| FUNCIONÁRIOS | 1 | Nome completo |
| SEGUNDA–SÁBADO | 2–7 | Valor da diária ou falta |
| DIAS | 8 | Total de dias trabalhados |
| BÔNUS | 9 | Bônus (quando aplicável) |
| **TOTAL** | **10** | **Total a receber — coluna lida** |

A primeira linha é ignorada (cabeçalho). Linhas com total R$ 0 ou nome contendo "total" são ignoradas automaticamente.

---

## Modelo de texto (placeholders)

O corpo do recibo usa um template configurável em **Configurações → Texto do recibo**.

| Placeholder | Substitui por |
|---|---|
| `[nome]` ou `[funcionario]` | Nome do funcionário |
| `[total]` ou `[valor]` | Valor por extenso em português |
| `[empresa]` | Nome da empresa |
| `[cnpj]` | CNPJ da empresa |
| `[cidade]` | Cidade da empresa |
| `[endereco]` | Endereço da empresa |
| `[data]` | Data do recibo formatada |

Se o campo ficar vazio, o texto padrão é usado automaticamente.

---

## Como rodar (desenvolvimento)

```bash
npm install
npm run dev        # Electron com HMR
npm run test       # 58 testes unitários
npm run build      # compila main + renderer + preload
```

---

## Como distribuir

```bash
npm run dist:win    # MSIX (Microsoft Store) + instalador NSIS (.exe)
npm run dist:msix   # apenas MSIX
npm run pack        # pasta não empacotada (para teste)
```

Veja [STORE_SETUP.md](STORE_SETUP.md) para o guia completo de publicação na Microsoft Store.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Shell | Electron 34 |
| Build | electron-vite 3 + Vite 6 |
| UI | React 19 + TypeScript strict |
| Estilo | CSS custom properties (design tokens) |
| PDF | pdf-lib |
| Excel | exceljs |
| Config | JSON em `app.getPath('userData')` |
| Testes | vitest |
| Packaging | electron-builder (NSIS + MSIX) |

---

## Segurança

- `contextIsolation: true` — renderer sem acesso direto ao Node.js
- `nodeIntegration: false` — sem `require()` no renderer
- Todos os inputs IPC validados em `src/main/ipc/handlers.ts`
- Nenhum dado coletado ou transmitido — processamento 100% local
- Dependência runtime `uuid` (via exceljs) fixada em `^14.0.0` via `overrides`
