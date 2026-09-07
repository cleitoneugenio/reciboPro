# ReciboPro

Gerador de recibos de prestação de serviço para Windows. Lê uma planilha Excel e gera, em um clique, um PDF com um recibo por funcionário — nome, valor, valor por extenso em português e data, prontos para imprimir e assinar.

**[Instalar na Microsoft Store →](https://apps.microsoft.com/detail/9PG33DDBKDTC)** · Grátis · Categoria Produtividade

---

## A história

O ReciboPro nasceu de uma tarefa de sábado numa cerâmica no interior do Ceará. Toda semana, ~18 recibos de pagamento feitos à mão: abrir a planilha de ponto, copiar nome, digitar valor, escrever o total por extenso, calcular, imprimir, repetir. Trabalho que não cansa pelo esforço — cansa pela repetição.

A primeira versão foi um script Python que lia a planilha, identificava quem trabalhou na semana, calculava o total, convertia o valor para texto por extenso e cuspia todos os recibos num único PDF. Dezoito recibos em segundos, todos certos. O que era um sábado inteiro virou um clique.

Depois veio o problema óbvio: era uma ferramenta que só quem sabe abrir um terminal conseguia usar — e ferramenta que só o autor usa é ferramenta pela metade. Interface gráfica, prévia em tempo real, dark mode. E, por fim, a constatação de que os dados da empresa estavam _hardcoded_ no código: para outra empresa usar, teria que editar o `.py`, instalar Python e regerar o executável. Isso não é produto, é script com uma interface na frente.

A V2 é a reescrita que resolve isso — Electron + React + TypeScript, empresa configurável pela interface, instalável em dois cliques, publicada na Microsoft Store. O relato completo está nos dois artigos:

- [Sábado de gestor: como automatizei os recibos de pagamento de uma cerâmica com Python](https://medium.com/@cleitoneugenio87/s%C3%A1bado-de-gestor-como-automatizei-os-recibos-de-pagamento-de-uma-cer%C3%A2mica-com-python-a006033e4457) — a V1
- [De script Python a app na Microsoft Store: a história completa do ReciboPro](https://medium.com/@cleitoneugenio87/de-script-python-a-app-na-microsoft-store-a-hist%C3%B3ria-completa-do-recibopro-f412f6cfd67c) — a V2 e a certificação

---

## De script a produto

| | **V1 — Python** | **V2 — Electron** |
|---|---|---|
| Status | Em produção na cerâmica | Publicada na Microsoft Store (15/06/2026) |
| Público | Uma empresa (dados fixos no código) | Qualquer empresa (config pela interface) |
| UI | Tkinter → customtkinter (dark mode) | React 19 + design tokens CSS, dark-first |
| Leitura `.xlsx` | pandas | exceljs |
| Geração de PDF | ReportLab | pdf-lib (JavaScript puro) |
| Valor por extenso | num2words | implementação própria (`src/shared/utils.ts`) |
| Distribuição | `GeradorRecibos.exe` (~40 MB, PyInstaller `--onefile`) | Instalador NSIS + pacote MSIX |
| Testes | 29 (pytest) | 58 (vitest) |

As duas versões convivem neste repositório — ver [Estrutura do repositório](#estrutura-do-repositório).

---

## Funcionalidades (V2)

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
- **Dados de exemplo embutidos** — testável em dois cliques, offline, sem digitar nem baixar nada

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

## Rodando em desenvolvimento (V2)

```bash
npm install
npm run dev        # Electron com HMR
npm run test       # 58 testes unitários (vitest)
npm run build      # tsc --noEmit + compila main + renderer + preload
```

### Distribuição

```bash
npm run dist:win    # MSIX (Microsoft Store) + instalador NSIS (.exe)
npm run dist:msix   # apenas MSIX
npm run pack        # pasta não empacotada (para teste)
```

Veja [STORE_SETUP.md](STORE_SETUP.md) para o guia completo de publicação na Microsoft Store e [ARCHITECTURE.md](ARCHITECTURE.md) para a arquitetura detalhada (processos Electron, IPC, geração de PDF, persistência).

### V1 (Python)

```bash
pip install -r requirements.txt
python gerar_recibos.py ponto_semana.xlsx        # abre a GUI já com a planilha carregada
```

Build do executável: `python -m PyInstaller GeradorRecibos.spec`.

---

## Stack (V2)

| Camada | Tecnologia |
|--------|-----------|
| Shell | Electron 34 |
| Build | electron-vite 3 + Vite 6 |
| UI | React 19 + TypeScript strict |
| Estilo | CSS custom properties (design tokens), dark-first |
| PDF | pdf-lib |
| Excel | exceljs |
| Config | JSON em `app.getPath('userData')` |
| Testes | vitest |
| Packaging | electron-builder (NSIS + MSIX) |

Por que sem backend Python na V2: manter Python implicaria dois runtimes (+60 MB), IPC por subprocesso e duas linguagens — sem ganho real para esta lógica. Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md#por-que-sem-python-backend).

---

## Bugs que valeram aprendizado

Os artigos documentam os mais traiçoeiros — os que não aparecem em tutorial porque só surgem em uso real:

- **`CTkLabel` que não esquecia a imagem (V1)** — trocar de aba disparava `TclError: image "pyimageN" doesn't exist` no painel de prévia. O `customtkinter` não chama `configure(image='')` quando a imagem passa a `None`; o widget Tk por baixo mantém a referência ao `PhotoImage` já coletado. Fix: limpar o widget interno direto antes de liberar a referência Python.
- **Trace de `BooleanVar` destruindo a lista (V1)** — ao limpar a lista, todos os traces eram removidos antes de destruir os widgets; o `CTkCheckBox.destroy()` tentava remover o próprio trace já removido, o `TclError` era silenciado e a lista apontava para um frame morto. Fix: guardar o `trace_id` exato e remover apenas o trace da aplicação.
- **`file.path` removido no Electron 32 (V2)** — o drag & drop parou de funcionar sem erro nenhum: `file.path` passou a retornar `undefined` silenciosamente. Fix: migrar para `webUtils.getPathForFile(file)`.
- **Preview da última folha esticando os recibos (V2)** — com 3 recibos por folha, a última folha com 2 renderizava cada recibo a 50% da altura em vez de 33%. O flex distribuía o espaço entre os filhos presentes. Fix: a página sempre renderiza `count` slots de altura fixa; os vazios ficam como `div` em branco.

---

## Estrutura do repositório

```
V1 (Python)
  gerar_recibos.py         — script + GUI (customtkinter)
  test_gerar_recibos.py    — 29 testes pytest
  GeradorRecibos.spec      — build PyInstaller
  gerar_logo.py            — geração de assets (baixa as fontes Playfair Display)
  requirements.txt

V2 (Electron)
  src/main/                — processo main: IPC, serviços de Excel e PDF, store
  src/preload/             — contextBridge (window.api tipado)
  src/renderer/            — React: onboarding, tela principal, configurações
  src/shared/              — tipos + valorPorExtenso, formatarData, applyTemplate
  tests/                   — 58 testes vitest
  resources/               — ícones, tiles APPX, planilha de exemplo embutida
  electron-builder.yml     — NSIS + MSIX

Docs
  ARCHITECTURE.md          — arquitetura V2 detalhada
  STORE_SETUP.md           — publicação na Microsoft Store
```

---

## Segurança e privacidade

- `contextIsolation: true` / `nodeIntegration: false` — renderer sem acesso ao Node.js
- Todos os inputs IPC validados com type guards em `src/main/ipc/handlers.ts`
- **Nenhum dado é coletado ou transmitido** — todo o processamento é 100% local
- Dependência runtime `uuid` (via exceljs) fixada em `^14.0.0` via `overrides`

---

## Licença e créditos

[MIT](LICENSE) © 2026 Cleiton Eugenio.

Desenvolvido por uma pessoa automatizando uma tarefa repetitiva do chão de fábrica, com IA como auxiliar onde o problema não tinha saída óbvia, e testes automatizados garantindo que nada quebra em silêncio.
