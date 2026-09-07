# ReciboPro — Microsoft Store Setup

Guia completo para publicar o ReciboPro na Microsoft Store.

---

## 1. Pré-requisitos

- Conta no [Microsoft Partner Center](https://partner.microsoft.com/dashboard) (taxa única de $19 USD)
- Windows 10/11 com Windows SDK instalado (para assinar o MSIX localmente em teste)

---

## 2. Configurar o Publisher CN

O campo `publisher` no `electron-builder.yml` deve ser **exatamente igual** ao que o Partner Center atribuiu à sua conta.

**Como obter:**
1. Acesse o Partner Center → Account Settings → Organization profile
2. Procure o campo **Publisher ID** ou **Publisher display name**
3. O CN no MSIX segue o formato: `CN=NomeExibido`

**Edite o arquivo `electron-builder.yml`:**
```yaml
appx:
  identityName: SuaNome.ReciboPro        # sem espaços, sem caracteres especiais
  publisher: "CN=Seu Nome Exato"          # EXATAMENTE como no Partner Center
  publisherDisplayName: Seu Nome
  displayName: ReciboPro
```

---

## 3. Registrar o app no Partner Center

1. Partner Center → Apps and Games → **New product** → App
2. Reserve o nome: **ReciboPro**
3. Anote o **Package identity name** gerado (ex: `A1B2C3DE.ReciboPro`)
4. Atualize `identityName` no `electron-builder.yml` com esse valor

---

## 4. Assets visuais obrigatórios

A Store exige imagens em tamanhos específicos. Coloque em `resources/appx-assets/`:

| Arquivo | Tamanho | Uso |
|---|---|---|
| `StoreLogo.png` | 50×50 | Ícone na Store |
| `Square44x44Logo.png` | 44×44 | Barra de tarefas |
| `Square150x150Logo.png` | 150×150 | Tile médio |
| `Square310x310Logo.png` | 310×310 | Tile grande |
| `Wide310x150Logo.png` | 310×150 | Tile largo |
| `SplashScreen.png` | 620×300 | Tela de splash |

Você tem o arquivo `resources/recibopro-icon-1024.png` como base. Use o [Image Resizer](https://www.microsoft.com/store/productId/9NBLGGH53WBJ) ou o site [makeappicon.com](https://makeappicon.com) para gerar os tamanhos acima.

---

## 5. Política de privacidade (obrigatória)

A Store exige uma URL de política de privacidade. O ReciboPro não coleta dados — use este texto:

```
ReciboPro não coleta, transmite nem armazena dados pessoais fora do computador do usuário.
Todos os arquivos (planilhas Excel e PDFs gerados) são processados localmente.
Nenhuma informação é enviada para servidores externos.
```

**Opção gratuita para hospedar:** Crie um repositório público no GitHub e use o GitHub Pages para servir um `privacy.html` com o texto acima. A URL ficaria: `https://seunome.github.io/recibopro-privacy`

---

## 6. Gerar o pacote MSIX

```bash
npm run dist:msix
```

O pacote será gerado em `dist/ReciboPro-{version}.appx`.

---

## 7. Submissão

1. Partner Center → Seu app → **Packages**
2. Upload do `.appx` ou `.msix` gerado
3. Preencha: descrição, capturas de tela (mínimo 1, recomendado 4-6), categoria (Produtividade)
4. Em **Properties** → Privacy Policy URL: coloque sua URL
5. Submit for certification

**Tempo de aprovação:** geralmente 1-3 dias úteis para a primeira submissão.

---

## 8. Scripts disponíveis

```bash
npm run dist:msix    # gera apenas o MSIX para a Store
npm run dist:win     # gera MSIX + instalador NSIS (.exe)
npm run pack         # gera pasta não empacotada (para teste rápido)
```
