# ReciboPro

Importe uma planilha `.xlsx`, escolha a semana e gere todos os recibos de prestação de serviço da equipe de uma vez — um por pessoa, com valor por extenso e data — num único PDF pronto para imprimir e assinar. Windows, grátis, sem cadastro.

![ReciboPro em uso](docs/recibopro-demo.gif)

**[Instalar na Microsoft Store →](https://apps.microsoft.com/detail/9PG33DDBKDTC)** · Grátis · Produtividade

---

## De um script de sábado a um app na Store

Todo sábado, a mesma rotina: abrir a planilha de ponto e montar recibo por recibo na mão — nome, valor, valor por extenso, data —, imprimir, repetir. Cerca de 18 por semana. Em algum momento no meio da pilha a conta não fecha: isso não devia ser feito assim.

A primeira versão foi um script Python. Lia a planilha, calculava os totais, escrevia os valores por extenso e montava todos os recibos num único PDF. Dezoito recibos em segundos — a manhã de sábado virou um clique.

Faltava tudo em volta do clique. O script rodava pela linha de comando e os dados da empresa estavam fixos no código: usar em outro lugar exigia editar o `.py`, instalar Python e regerar o `.exe`. Era um script com uma interface na frente, não um produto.

A **V2** fecha essa lacuna — reescrita em Electron + React + TypeScript, com a empresa configurável pela própria interface e instalação em dois cliques. Foi publicada na Microsoft Store em junho de 2026, depois de seis reprovações de certificação. A ideia é a mesma; agora serve qualquer pequena empresa.

O caminho completo está em dois artigos: [a V1 em Python](https://medium.com/@cleitoneugenio87/s%C3%A1bado-de-gestor-como-automatizei-os-recibos-de-pagamento-de-uma-cer%C3%A2mica-com-python-a006033e4457) e [a V2 e a certificação na Store](https://medium.com/@cleitoneugenio87/de-script-python-a-app-na-microsoft-store-a-hist%C3%B3ria-completa-do-recibopro-f412f6cfd67c).

---

## V1 e V2 lado a lado

| | **V1 — Python** | **V2 — Electron** |
|---|---|---|
| Status | Descontinuada — mantida como histórico em [`legacy-v1/`](legacy-v1/) | **Ativa** — publicada na Microsoft Store (15/06/2026) |
| Público | Uma empresa (dados fixos no código) | Qualquer empresa (config pela interface) |
| UI | Tkinter → customtkinter (dark mode) | React 19 + design tokens CSS, dark-first |
| Leitura `.xlsx` | pandas | exceljs |
| Geração de PDF | ReportLab | pdf-lib (JavaScript puro) |
| Valor por extenso | num2words | implementação própria (`src/shared/utils.ts`) |
| Distribuição | `GeradorRecibos.exe` (~40 MB, PyInstaller `--onefile`) | Instalador NSIS + pacote MSIX |
| Testes | 29 (pytest) | 59 (vitest) |

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
npm run test       # 59 testes unitários (vitest)
npm run build      # tsc --noEmit + compila main + renderer + preload
```

### Distribuição

```bash
npm run dist:win    # MSIX (Microsoft Store) + instalador NSIS (.exe)
npm run dist:msix   # apenas MSIX
npm run pack        # pasta não empacotada (para teste)
```

Veja [docs/STORE_SETUP.md](docs/STORE_SETUP.md) para o guia completo de publicação na Microsoft Store e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para a arquitetura detalhada (processos Electron, IPC, geração de PDF, persistência).

### V1 (Python) — histórico

O código da V1 vive em [`legacy-v1/`](legacy-v1/) e não é mais mantido. Os dados da empresa (nome, CNPJ, endereço) foram substituídos por valores de exemplo — ajuste as constantes no topo de `legacy-v1/gerar_recibos.py` ou defina as variáveis de ambiente `RECIBO_EMPRESA`, `RECIBO_CNPJ`, `RECIBO_SEDE`, `RECIBO_CIDADE`.

```bash
cd legacy-v1
pip install -r requirements.txt
python gerar_recibos.py ponto_semana.xlsx        # abre a GUI já com a planilha carregada
python -m PyInstaller GeradorRecibos.spec         # build do executável
```

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

Por que sem backend Python na V2: manter Python implicaria dois runtimes (+60 MB), IPC por subprocesso e duas linguagens — sem ganho real para esta lógica. Detalhes em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#por-que-sem-python-backend).

---

## Bugs que valeram aprendizado

Os artigos documentam os mais traiçoeiros — os que não aparecem em tutorial porque só surgem em uso real:

- **`CTkLabel` que não esquecia a imagem (V1)** — trocar de aba disparava `TclError: image "pyimageN" doesn't exist` no painel de prévia. O `customtkinter` não chama `configure(image='')` quando a imagem passa a `None`; o widget Tk por baixo mantém a referência ao `PhotoImage` já coletado. Fix: limpar o widget interno direto antes de liberar a referência Python.
- **Trace de `BooleanVar` destruindo a lista (V1)** — ao limpar a lista, todos os traces eram removidos antes de destruir os widgets; o `CTkCheckBox.destroy()` tentava remover o próprio trace já removido, o `TclError` era silenciado e a lista apontava para um frame morto. Fix: guardar o `trace_id` exato e remover apenas o trace da aplicação.
- **`file.path` removido no Electron 32 (V2)** — o drag & drop parou de funcionar sem erro nenhum: `file.path` passou a retornar `undefined` silenciosamente. Fix: migrar para `webUtils.getPathForFile(file)`.
- **Preview da última folha esticando os recibos (V2)** — com 3 recibos por folha, a última folha com 2 renderizava cada recibo a 50% da altura em vez de 33%. O flex distribuía o espaço entre os filhos presentes. Fix: a página sempre renderiza `count` slots de altura fixa; os vazios ficam como `div` em branco.

---

## Estrutura do repositório

A raiz é a aplicação **V2** (layout padrão electron-vite). O restante está organizado em pastas:

```
.                          raiz = V2 (Electron)
├── src/
│   ├── main/              processo main: IPC, serviços de Excel e PDF, store
│   ├── preload/           contextBridge (window.api tipado)
│   ├── renderer/          React: onboarding, tela principal, configurações
│   └── shared/            tipos + valorPorExtenso, formatarData, applyTemplate
├── tests/                 59 testes vitest
├── resources/             ícones, tiles APPX, planilha de exemplo embutida
├── electron-builder.yml   NSIS + MSIX
│
├── docs/
│   ├── ARCHITECTURE.md              arquitetura V2 detalhada
│   ├── STORE_SETUP.md               publicação na Microsoft Store
│   └── documentacao_recibopro_v2.md documentação longa da V2
│
├── store-assets/          imagens da listagem da Microsoft Store (não vão no build)
│
└── legacy-v1/             V1 em Python — histórico, sem manutenção
    ├── gerar_recibos.py        script + GUI (customtkinter)
    ├── test_gerar_recibos.py   29 testes pytest
    ├── GeradorRecibos.spec     build PyInstaller
    ├── gerar_logo.py / gerar_icone.py / gerar_documentacao.py / gerar_doc_v2.py
    └── requirements.txt
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
