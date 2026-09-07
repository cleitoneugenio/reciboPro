#!/usr/bin/env python3
"""
Gera a documentação do projeto gerar_recibos.py em PDF.
Uso: python gerar_documentacao.py
"""

import os
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Dracula Theme — cores exatas do tema usado no VS Code
# ---------------------------------------------------------------------------
_BG        = '#282a36'   # fundo
_FG        = '#f8f8f2'   # texto padrão
_COMMENT   = '#6272a4'   # comentários
_KEYWORD   = '#ff79c6'   # palavras-chave (pink)
_BUILTIN   = '#8be9fd'   # built-ins / tipos (cyan)
_STRING    = '#f1fa8c'   # strings (yellow)
_NUMBER    = '#bd93f9'   # números (purple)
_FUNCTION  = '#50fa7b'   # nome de função/classe após def/class (green)
_OPERATOR  = '#ff79c6'   # operadores

_PY_KEYWORDS = frozenset({
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
    'while', 'with', 'yield',
})

_PY_BUILTINS = frozenset({
    'int', 'str', 'float', 'list', 'dict', 'tuple', 'set', 'bool',
    'len', 'range', 'print', 'type', 'isinstance', 'hasattr', 'getattr',
    'open', 'super', 'object', 'Exception', 'ValueError', 'TypeError',
    'round', 'abs', 'min', 'max', 'enumerate', 'zip', 'sorted',
})

# Tokenizer: comentário > string > número > palavra > resto
_TOKEN_RE = re.compile(
    r'(?P<comment>#[^\n]*)'
    r"|(?P<string>[fFrRbB]{0,2}(?:'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))"
    r'|(?P<number>\b\d+\.?\d*\b)'
    r'|(?P<word>[A-Za-z_]\w*)'
    r'|(?P<other>[^\w\s\'\"#]+|[ \t]+)'
)


def _xml_esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _colorir_linha(linha: str) -> str:
    """Tokeniza e aplica cores do Dracula Theme a uma linha de código."""
    if not linha.strip():
        return '&nbsp;'

    n = len(linha) - len(linha.lstrip(' '))
    indent = '&nbsp;' * n
    texto = linha.lstrip(' ')

    parts = []
    after_def = False   # True após 'def' ou 'class' → próxima palavra fica verde

    for m in _TOKEN_RE.finditer(texto):
        kind = m.lastgroup
        val  = m.group()
        esc  = _xml_esc(val)

        if kind == 'comment':
            parts.append(f'<font color="{_COMMENT}">{esc}</font>')
            after_def = False

        elif kind == 'string':
            parts.append(f'<font color="{_STRING}">{esc}</font>')
            after_def = False

        elif kind == 'number':
            parts.append(f'<font color="{_NUMBER}">{esc}</font>')
            after_def = False

        elif kind == 'word':
            if after_def:
                parts.append(f'<font color="{_FUNCTION}">{esc}</font>')
                after_def = False
            elif val in _PY_KEYWORDS:
                parts.append(f'<font color="{_KEYWORD}">{esc}</font>')
                after_def = val in ('def', 'class')
            elif val in _PY_BUILTINS:
                parts.append(f'<font color="{_BUILTIN}">{esc}</font>')
                after_def = False
            else:
                parts.append(f'<font color="{_FG}">{esc}</font>')
                after_def = False

        else:  # whitespace ou operadores
            parts.append(esc)
            if val.strip():   # operador (não espaço) → reseta after_def
                after_def = False

    return indent + ''.join(parts)


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------

def criar_estilos() -> dict:
    return {
        'capa_titulo': ParagraphStyle(
            'capa_titulo',
            fontName='Helvetica-Bold',
            fontSize=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=10,
        ),
        'capa_sub': ParagraphStyle(
            'capa_sub',
            fontName='Helvetica',
            fontSize=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#444444'),
            spaceAfter=6,
        ),
        'secao': ParagraphStyle(
            'secao',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=colors.HexColor('#1a1a2e'),
            spaceBefore=18,
            spaceAfter=6,
            borderPad=4,
        ),
        'subsecao': ParagraphStyle(
            'subsecao',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#2e4057'),
            spaceBefore=10,
            spaceAfter=4,
        ),
        'corpo': ParagraphStyle(
            'corpo',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_JUSTIFY,
            leading=16,
            spaceAfter=6,
        ),
        # Texto dentro do bloco de código — Dracula Theme
        'codigo_dark': ParagraphStyle(
            'codigo_dark',
            fontName='Courier',
            fontSize=9,
            leading=15,
            textColor=colors.HexColor(_FG),
            spaceBefore=0,
            spaceAfter=0,
        ),
        'topico': ParagraphStyle(
            'topico',
            fontName='Helvetica',
            fontSize=10,
            leading=16,
            leftIndent=14,
            spaceAfter=3,
        ),
        'rodape': ParagraphStyle(
            'rodape',
            fontName='Helvetica',
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey,
        ),
        # Estilos para células de tabela (necessário para quebra automática de linha)
        'celula': ParagraphStyle(
            'celula',
            fontName='Helvetica',
            fontSize=8,
            leading=12,
            spaceAfter=0,
            spaceBefore=0,
        ),
        'celula_h': ParagraphStyle(
            'celula_h',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=12,
            textColor=colors.white,
            spaceAfter=0,
            spaceBefore=0,
        ),
    }


# ---------------------------------------------------------------------------
# Constante de largura útil: A4 (21cm) - 2 * 2.2cm de margem
# ---------------------------------------------------------------------------
LARGURA_UTIL = 16.6 * cm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def divisor(cor=colors.HexColor('#cccccc')) -> list:
    return [
        Spacer(1, 0.3 * cm),
        HRFlowable(width='100%', thickness=0.5, color=cor),
        Spacer(1, 0.3 * cm),
    ]


def bloco_codigo(linhas: list, s: dict) -> list:
    """Bloco de código com Dracula Theme: fundo #282a36, syntax highlighting completo."""
    html = '<br/>'.join(_colorir_linha(l) for l in linhas)
    tabela = Table(
        [[Paragraph(html, s['codigo_dark'])]],
        colWidths=[LARGURA_UTIL],
    )
    tabela.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor(_BG)),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
        ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#44475a')),
    ]))
    return [Spacer(1, 0.2 * cm), tabela, Spacer(1, 0.2 * cm)]


def imagem_proporcional(nome_arquivo: str, largura: float, s: dict, legenda: str = '') -> list:
    """Insere imagem mantendo proporção original. Retorna lista de flowables."""
    caminho = os.path.join(_DIR, nome_arquivo)
    pil = PILImage.open(caminho)
    w, h = pil.size
    altura = largura * (h / w)
    elementos = [
        Spacer(1, 0.3 * cm),
        Image(caminho, width=largura, height=altura),
    ]
    if legenda:
        estilo = ParagraphStyle(
            'legenda',
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=6,
        )
        elementos.append(Paragraph(legenda, estilo))
    elementos.append(Spacer(1, 0.3 * cm))
    return elementos


def mk_tabela(dados_raw: list, col_widths: list, cor_header, s: dict) -> Table:
    """Cria tabela com Paragraph em todas as células para quebra automática de texto."""
    dados = []
    for i, linha in enumerate(dados_raw):
        estilo = s['celula_h'] if i == 0 else s['celula']
        dados.append([Paragraph(str(cel), estilo) for cel in linha])
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  cor_header),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
        ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('BOX',            (0, 0), (-1, -1), 0.8, colors.HexColor('#999999')),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',     (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 6),
        ('LEFTPADDING',    (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 7),
    ]))
    return tabela


# ---------------------------------------------------------------------------
# Seções do documento
# ---------------------------------------------------------------------------

def secao_capa(s: dict) -> list:
    return [
        Spacer(1, 2 * cm),
        Paragraph('DOCUMENTAÇÃO TÉCNICA', s['capa_titulo']),
        Paragraph('Gerador de Recibos de Prestação de Serviço', s['capa_sub']),
        Spacer(1, 0.4 * cm),
        HRFlowable(width='60%', thickness=2, color=colors.HexColor('#1a1a2e'), hAlign='CENTER'),
        Spacer(1, 0.6 * cm),
        Paragraph('Arquivo: <b>gerar_recibos.py</b>', s['capa_sub']),
        Paragraph('Linguagem: <b>Python 3</b>', s['capa_sub']),
        Paragraph('Bibliotecas: <b>customtkinter · pandas · ReportLab · Pillow · num2words</b>', s['capa_sub']),
        Spacer(1, 3 * cm),
        Paragraph(
            'Este documento explica passo a passo como o programa foi construído, '
            'o motivo de cada escolha técnica e como utilizá-lo no dia a dia.',
            s['corpo'],
        ),
    ]


def secao_objetivo(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('1. OBJETIVO DO PROGRAMA', s['secao']),
        Paragraph(
            'O programa nasceu da necessidade de eliminar o trabalho manual de criar '
            'recibos de pagamento toda semana para os funcionários da empresa '
            '<b>GF MUNIZ ARTEFACTOS DE CERAMICA EIRELI</b>.',
            s['corpo'],
        ),
        Paragraph(
            'Toda semana existe uma planilha Excel (<b>.xlsx</b>) com os nomes dos '
            'funcionários e os valores de diária de segunda a sábado. O programa lê '
            'essa planilha automaticamente e gera um único arquivo PDF com todos os '
            'recibos prontos para impressão e assinatura.',
            s['corpo'],
        ),
        Paragraph('<b>Problema resolvido:</b>', s['subsecao']),
        Paragraph('• Criar recibo por recibo manualmente levava muito tempo.', s['topico']),
        Paragraph('• Risco de erro humano ao copiar nomes e valores.', s['topico']),
        Paragraph('• Dificuldade em escrever o valor por extenso corretamente.', s['topico']),
        Paragraph('<b>Solução entregue:</b>', s['subsecao']),
        Paragraph('• Um único comando gera os ~20 recibos em segundos.', s['topico']),
        Paragraph('• Valor por extenso gerado automaticamente em português.', s['topico']),
        Paragraph('• Data preenchida automaticamente com o dia da geração.', s['topico']),
        Paragraph('• Funcionários sem trabalho na semana são ignorados automaticamente.', s['topico']),
    ]


def secao_bibliotecas(s: dict) -> list:
    dados_tabela = [
        ['Biblioteca', 'Versão', 'Para que serve', 'Por que foi escolhida'],
        ['customtkinter', '5.2.2', 'Interface gráfica moderna (dark mode)', 'Wrapper sobre tkinter com widgets modernos, dark/light theme, sem dependência de sistema'],
        ['pandas', '3.0.2', 'Ler e processar o arquivo .xlsx', 'Biblioteca padrão para dados em Python; lida com Excel de forma simples e robusta'],
        ['openpyxl', '—', 'Motor de leitura de arquivos .xlsx', 'Exigida pelo pandas para abrir arquivos Excel modernos; instalada automaticamente'],
        ['Pillow', '12.2.0', 'Renderizar a prévia do recibo como imagem', 'Biblioteca de imagem mais completa do ecossistema Python; suporte a fontes TrueType'],
        ['ReportLab', '4.4.10', 'Gerar o arquivo PDF', 'Biblioteca profissional para criação de PDFs em Python; permite controle total do layout'],
        ['num2words', '0.5.14', 'Converter número em texto por extenso', 'Suporte nativo ao português brasileiro (pt_BR); preciso e fácil de usar'],
        ['os / sys / threading / logging', '—', 'Arquivos, threads, argumentos CLI e log', 'Módulos nativos do Python; sem instalação extra'],
        ['datetime', '—', 'Obter a data atual do sistema', 'Módulo nativo do Python; fornece a data de geração do recibo automaticamente'],
    ]

    tabela = mk_tabela(
        dados_tabela,
        [2.8 * cm, 1.5 * cm, 4.0 * cm, 8.3 * cm],
        colors.HexColor('#1a1a2e'),
        s,
    )

    return [
        *divisor(),
        Paragraph('2. BIBLIOTECAS UTILIZADAS', s['secao']),
        Paragraph(
            'As versões exatas estão fixadas em <b>requirements.txt</b>. Para instalar:',
            s['corpo'],
        ),
        *bloco_codigo(
            ['pip install -r requirements.txt'],
            s,
        ),
        Paragraph('Ou manualmente:', s['corpo']),
        *bloco_codigo(
            ['pip install customtkinter==5.2.2 num2words==0.5.14 pandas==3.0.2 Pillow==12.2.0 reportlab==4.4.10'],
            s,
        ),
        Spacer(1, 0.4 * cm),
        tabela,
    ]


def secao_estrutura(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('3. ESTRUTURA DO PROGRAMA', s['secao']),
        Paragraph(
            'O programa é dividido em funções, cada uma com uma responsabilidade '
            'específica. Essa separação torna o código mais fácil de entender, '
            'testar e modificar no futuro.',
            s['corpo'],
        ),

        Paragraph('3.1 — valor_por_extenso(valor)', s['subsecao']),
        Paragraph(
            'Recebe um número (ex: <b>395.0</b>) e retorna uma string formatada com '
            'o valor em reais e o texto por extenso em português.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def valor_por_extenso(valor: float) -> str:',
            '    reais = int(valor)',
            '    centavos = round((valor - reais) * 100)',
            "    extenso = num2words(reais, lang='pt_BR') + ' reais'",
            '    if centavos > 0:',
            "        extenso += ' e ' + num2words(centavos, lang='pt_BR') + ' centavos'",
            "    valor_fmt = f'R$ {valor:,.2f}'.replace(',','X').replace('.',',').replace('X','.')",
            "    return f'{valor_fmt} ({extenso})'",
        ], s),
        Paragraph(
            '<b>Por que assim?</b> O formato brasileiro usa vírgula como separador decimal '
            '(R$ 395,00), mas o Python usa ponto. Por isso fazemos a substituição manualmente: '
            'primeiro trocamos a vírgula por "X" (temporário), depois o ponto por vírgula, '
            'e por fim o "X" por ponto — resultando no padrão correto.',
            s['corpo'],
        ),

        Paragraph('3.2 — formatar_data(data)', s['subsecao']),
        Paragraph(
            'Converte um objeto <b>datetime</b> para o formato por extenso em português, '
            'como: <b>11 de abril de 2026</b>.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def formatar_data(data: datetime) -> str:',
            "    meses = ['janeiro', 'fevereiro', 'março', ...]",
            "    return f'{data.day} de {meses[data.month - 1]} de {data.year}'",
        ], s),
        Paragraph(
            '<b>Por que assim?</b> O Python não tem suporte nativo a nomes de meses em '
            'português sem configurar o locale do sistema operacional (o que pode falhar '
            'dependendo do Windows). A lista manual garante que funciona em qualquer máquina.',
            s['corpo'],
        ),

        Paragraph('3.3 — ler_funcionarios(arquivo, sheet_name)', s['subsecao']),
        Paragraph(
            'Lê o arquivo <b>.xlsx</b> com o pandas e retorna uma lista com nome e total '
            'de cada funcionário que trabalhou na semana. O parâmetro <b>sheet_name</b> '
            'indica qual aba da planilha deve ser lida (padrão: primeira aba).',
            s['corpo'],
        ),
        *bloco_codigo([
            'def ler_funcionarios(arquivo: str, sheet_name=0) -> list:',
            '    df = pd.read_excel(arquivo, sheet_name=sheet_name, header=0)',
            '    for _, row in df.iterrows():',
            '        try:',
            '            int(row.iloc[0])   # col 0 = número do funcionário',
            '        except (ValueError, TypeError):',
            '            continue           # pula cabeçalho e linha TOTAL',
            '        nome  = str(row.iloc[1]).strip()   # col 1 = nome',
            '        total = float(row.iloc[10])        # col 10 = total',
            '        if total <= 0: continue',
            "        funcionarios.append({'nome': nome, 'total': total})",
        ], s),
        Paragraph(
            '<b>Por que sheet_name=0 como padrão?</b> O valor 0 instrui o pandas a ler a '
            'primeira aba, mantendo compatibilidade com o modo CLI (que não passa aba). '
            'Quando a GUI seleciona uma aba pelo nome, passa a string correspondente.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que header=0?</b> A planilha tem uma linha de título no topo '
            '("CONTROLE DE PONTO...") que o pandas usa automaticamente como nome das colunas. '
            'Isso nos permite identificar as linhas de dados pelo conteúdo da primeira coluna.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que tentar converter col[0] para int?</b> As linhas de dados têm '
            'número de funcionário (1, 2, 3...). A linha de cabeçalho tem "#" e a linha '
            'final tem "TOTAL" — ambas falham no int() e são ignoradas automaticamente.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que ignorar total <= 0?</b> Funcionários que não trabalharam nenhum dia '
            'na semana ficam com total zero. Não faz sentido gerar recibo de R$ 0,00.',
            s['corpo'],
        ),

        Paragraph('3.4 — montar_recibo(nome, total, data_str, styles)', s['subsecao']),
        Paragraph(
            'Monta a lista de elementos visuais de um recibo individual: título, '
            'texto do corpo, linha de assinatura e nome do funcionário.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def montar_recibo(...) -> list:',
            '    return [',
            "        Paragraph('<u><b>RECIBO DE PRESTAÇÃO DE SERVIÇO</b></u>', titulo),",
            '        Spacer(1, 0.5 * cm),',
            '        Paragraph(corpo_texto, corpo),',
            '        Spacer(1, 0.4 * cm),',
            "        Paragraph(f'Bela Cruz, {data_str}.', corpo),",
            '        Spacer(1, 1.8 * cm),',
            "        HRFlowable(width='55%', ...),   # linha de assinatura",
            '        Spacer(1, 0.25 * cm),',
            '        Paragraph(nome, assinatura),',
            '    ]',
        ], s),
        Paragraph(
            '<b>Por que retornar uma lista?</b> O ReportLab trabalha com uma lista de '
            '"flowables" (elementos que fluem pela página). Retornar a lista permite '
            'envolvê-la em um <b>KeepTogether</b>, que garante que os elementos de um '
            'mesmo recibo nunca sejam separados entre duas páginas.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que &lt;u&gt; e &lt;b&gt; no título?</b> O ReportLab aceita '
            'marcação XML dentro do texto dos parágrafos. A tag &lt;u&gt; aplica '
            'sublinhado e &lt;b&gt; aplica negrito — exatamente o formato pedido para o título.',
            s['corpo'],
        ),

        Paragraph('3.5 — gerar_pdf_de_lista(funcionarios, arquivo_pdf)', s['subsecao']),
        Paragraph(
            'Recebe uma lista de funcionários já carregada (e opcionalmente filtrada pela GUI) '
            'e constrói o PDF. Essa separação permite que a GUI filtre os funcionários por '
            'checkboxes antes de chamar a geração, sem duplicar a lógica de montagem do PDF.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def gerar_pdf_de_lista(funcionarios: list, arquivo_pdf: str) -> None:',
            '    if not funcionarios:',
            "        raise ValueError('Nenhum funcionário selecionado.')",
            '    hoje = datetime.today()',
            '    doc = SimpleDocTemplate(arquivo_pdf, pagesize=A4, ...)',
            '    story = []',
            '    for i, func in enumerate(funcionarios):',
            '        recibo = montar_recibo(...)',
            '        story.append(KeepTogether(recibo))     # mantém recibo unido',
            '        if i < len(funcionarios) - 1:',
            '            story.append(HRFlowable(dash=(6,4)))  # linha tracejada',
            '    doc.build(story)',
        ], s),
        Paragraph(
            '<b>Por que separar de gerar_pdf?</b> A função <i>gerar_pdf</i> original '
            'chama <i>ler_funcionarios</i> internamente — boa para CLI. Mas na GUI '
            'já carregamos a lista para exibir os checkboxes; passar a lista diretamente '
            'evita ler o arquivo Excel duas vezes e permite o filtro por seleção.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que KeepTogether?</b> Sem ele, um recibo poderia ser cortado no meio '
            'entre uma página e outra. O KeepTogether move o bloco inteiro para a página '
            'seguinte caso não caiba no espaço restante.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que a linha tracejada (dash)?</b> Serve como guia visual para separar '
            'os recibos ao imprimir e recortar, facilitando a distribuição para cada funcionário.',
            s['corpo'],
        ),

        Paragraph('3.6 — gerar_pdf(arquivo_xlsx, arquivo_pdf)', s['subsecao']),
        Paragraph(
            'Mantida para compatibilidade com o modo CLI. Lê os funcionários internamente '
            'e delega a construção do PDF para <b>gerar_pdf_de_lista</b>.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def gerar_pdf(arquivo_xlsx, arquivo_pdf):',
            '    funcionarios = ler_funcionarios(arquivo_xlsx)',
            '    if not funcionarios:',
            "        log.warning('Nenhum funcionário encontrado.')",
            '        sys.exit(1)',
            '    gerar_pdf_de_lista(funcionarios, arquivo_pdf)',
        ], s),

        Paragraph('3.7 — gerar_preview_pil(funcionario, width)', s['subsecao']),
        Paragraph(
            'Renderiza um recibo individual como imagem PIL — usado exclusivamente '
            'pelo painel de prévia da GUI. Produz exatamente o mesmo layout do PDF '
            '(mesmos espaçadores, mesmas proporções, mesma linha de assinatura) '
            'escalado para a largura do painel.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def gerar_preview_pil(funcionario: dict, width: int = 420):',
            '    from PIL import Image, ImageDraw, ImageFont',
            '    # Escala proporcional à largura de conteúdo do A4 (481.9pt)',
            '    scale = width / 481.9',
            '    img  = Image.new("RGB", (width, height_estimado), "#ffffff")',
            '    draw = ImageDraw.Draw(img)',
            '    # Renderiza título, corpo, data, linha de assinatura e nome',
            '    # usando wrap de palavras em pixels (_wrap_px)',
            '    return img.crop((0, 0, width, y_final))',
        ], s),
        Paragraph(
            '<b>Por que PIL e não ReportLab?</b> O ReportLab gera apenas PDF — '
            'não tem API para exportar página como imagem. O PIL permite renderizar '
            'diretamente em bitmap, que o CTkImage do customtkinter exibe na tela.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que rodar em thread?</b> O PIL pode levar 100–300ms por renderização '
            'dependendo da resolução. Rodar na thread principal travaria a UI. A função '
            'é chamada de dentro de um <i>threading.Thread</i> com um mecanismo de token '
            'para descartar renders desatualizados (ver seção de bugs resolvidos).',
            s['corpo'],
        ),

        Paragraph('3.8 — resource_path(filename)', s['subsecao']),
        Paragraph(
            'Retorna o caminho correto para arquivos de recurso (ícone, logo) tanto '
            'ao rodar como script quanto dentro do executável PyInstaller.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def resource_path(filename: str) -> str:',
            '    base = getattr(sys, "_MEIPASS",',
            '                   os.path.dirname(os.path.abspath(__file__)))',
            '    return os.path.join(base, filename)',
        ], s),
        Paragraph(
            'Dentro do <i>.exe</i> gerado pelo PyInstaller (<i>--onefile</i>), os '
            'recursos são extraídos para <i>sys._MEIPASS</i> em tempo de execução. '
            'Como script, usa o diretório do próprio arquivo. O <i>getattr</i> com '
            'fallback elimina qualquer if/else explícito.',
            s['corpo'],
        ),

        Paragraph('3.9 — setup_logging()', s['subsecao']),
        Paragraph(
            'Configura o sistema de log persistente em arquivo rotativo. '
            'Chamada uma única vez no bloco <i>if __name__ == "__main__"</i>.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def setup_logging() -> str:',
            '    app_dir = os.path.join(os.environ["APPDATA"], "GeradorRecibos")',
            '    os.makedirs(app_dir, exist_ok=True)',
            '    fh = logging.handlers.RotatingFileHandler(',
            '        log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8"',
            '    )',
            '    # Root logger em WARNING — suprime ruído de bibliotecas externas',
            '    logging.getLogger().setLevel(logging.WARNING)',
            '    # Loggers da aplicação em DEBUG',
            '    for name in ("gerar_recibos", "__main__"):',
            '        logging.getLogger(name).setLevel(logging.DEBUG)',
        ], s),
        Paragraph(
            '<b>Por que root logger em WARNING?</b> Pandas, Pillow e outras bibliotecas '
            'emitem mensagens DEBUG/INFO internas sem interesse para diagnóstico do '
            'programa. Manter o root em WARNING suprime esse ruído; os loggers da '
            'aplicação em DEBUG capturam tudo que importa.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que configurar tanto "gerar_recibos" quanto "__main__"?</b> '
            'O objeto <i>log = logging.getLogger(__name__)</i> no topo do arquivo '
            'recebe o nome <i>"gerar_recibos"</i> quando importado como módulo, '
            'mas <i>"__main__"</i> quando executado diretamente. Configurar ambos '
            'garante cobertura nos dois modos.',
            s['corpo'],
        ),

        Paragraph('3.10 — main()', s['subsecao']),
        Paragraph(
            'Ponto de entrada do programa. Lê os argumentos passados na linha de comando '
            'e chama a função gerar_pdf.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def main():',
            '    arquivo_xlsx = sys.argv[1]',
            '    arquivo_pdf  = sys.argv[2] if len(sys.argv) >= 3 else',
            "                   os.path.splitext(arquivo_xlsx)[0] + '_recibos.pdf'",
            '    gerar_pdf(arquivo_xlsx, arquivo_pdf)',
        ], s),
        Paragraph(
            '<b>Por que sys.argv?</b> Permite passar o nome do arquivo diretamente no '
            'terminal, tornando o programa flexível para trabalhar com qualquer planilha '
            '— não só a da semana atual.',
            s['corpo'],
        ),
    ]


def secao_layout(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('4. LAYOUT E ESTILOS DO PDF', s['secao']),
        Paragraph(
            'O ReportLab utiliza o conceito de <b>ParagraphStyle</b> para definir a '
            'aparência de cada bloco de texto. Três estilos foram criados:',
            s['corpo'],
        ),
        Paragraph('• <b>titulo</b> — Helvetica-Bold, 13pt, centralizado.', s['topico']),
        Paragraph('• <b>corpo</b> — Helvetica, 10pt, justificado, entrelinha 15pt.', s['topico']),
        Paragraph('• <b>assinatura</b> — Helvetica, 10pt, centralizado.', s['topico']),
        Spacer(1, 0.3 * cm),
        Paragraph(
            'A página usa margens de <b>2 cm</b> nas laterais e <b>1,5 cm</b> no topo e '
            'rodapé, aproveitando bem o espaço do A4 para caber o maior número possível '
            'de recibos por página (em média 2 a 3, dependendo do comprimento do nome).',
            s['corpo'],
        ),
    ]


def secao_uso(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('5. COMO USAR O PROGRAMA', s['secao']),

        Paragraph('Opção 1 — Interface gráfica (recomendado)', s['subsecao']),
        Paragraph(
            'Execute o <b>GeradorRecibos.exe</b> com dois cliques (ou <i>python gerar_recibos.py</i> '
            'sem argumentos). A janela abre automaticamente.',
            s['corpo'],
        ),
        Paragraph('1. Clique em <b>⋯</b> ao lado de <b>PLANILHA</b> e selecione o arquivo <b>.xlsx</b>.', s['topico']),
        Paragraph('2. No campo <b>ABA</b>, selecione a semana desejada (preenchido automaticamente com a primeira aba).', s['topico']),
        Paragraph('3. No painel <b>FUNCIONÁRIOS</b>, marque ou desmarque quem deve entrar no PDF.', s['topico']),
        Paragraph('4. O painel <b>PRÉVIA</b> à direita mostra o recibo do funcionário selecionado — navegue com ← →.', s['topico']),
        Paragraph('5. Clique em <b>Gerar Recibos</b>. Ao concluir, o programa pergunta se deseja abrir o PDF.', s['topico']),

        Paragraph('Opção 2 — Linha de comando', s['subsecao']),
        Paragraph('<b>Opção A</b> — O PDF é gerado com o mesmo nome da planilha:', s['topico']),
        *bloco_codigo(['python gerar_recibos.py ponto_cedan_semana.xlsx'], s),
        Paragraph('<b>Opção B</b> — Definindo o nome do PDF de saída:', s['topico']),
        *bloco_codigo(['python gerar_recibos.py ponto_cedan_semana.xlsx recibos_semana1.pdf'], s),

        Paragraph('Instalar as dependências (apenas uma vez — modo script)', s['subsecao']),
        *bloco_codigo(['pip install -r requirements.txt'], s),

        Paragraph('Regras automáticas do programa', s['subsecao']),
        Paragraph('• Funcionários com total R$ 0,00 são ignorados (não gera recibo).', s['topico']),
        Paragraph('• A data é sempre a do dia em que o programa é executado.', s['topico']),
        Paragraph('• O valor por extenso é calculado automaticamente em português.', s['topico']),
        Paragraph('• Se um recibo não couber na página atual, vai para a próxima.', s['topico']),
    ]


def secao_estrutura_planilha(s: dict) -> list:
    dados_tabela = [
        ['Coluna', 'Índice', 'Conteúdo esperado'],
        ['#', '0', 'Número do funcionário (inteiro). Usado para identificar linhas de dados.'],
        ['FUNCIONÁRIOS', '1', 'Nome completo do funcionário.'],
        ['SEGUNDA', '2', 'Valor da diária ou "F" (falta).'],
        ['TERÇA', '3', 'Valor da diária ou "F" (falta).'],
        ['QUARTA', '4', 'Valor da diária ou "F" (falta).'],
        ['QUINTA', '5', 'Valor da diária ou "F" (falta).'],
        ['SEXTA', '6', 'Valor da diária ou "F" (falta).'],
        ['SÁBADO', '7', 'Valor da diária ou "F" (falta).'],
        ['DIAS', '8', 'Total de dias trabalhados.'],
        ['BÔNUS', '9', 'Bônus (quando aplicável).'],
        ['TOTAL', '10', 'Total a receber. É este valor que aparece no recibo.'],
    ]

    tabela = mk_tabela(
        dados_tabela,
        [2.8 * cm, 1.8 * cm, 12.0 * cm],
        colors.HexColor('#2e4057'),
        s,
    )

    return [
        *divisor(),
        Paragraph('6. ESTRUTURA ESPERADA DA PLANILHA', s['secao']),
        Paragraph(
            'O programa foi desenvolvido para ler planilhas no seguinte formato:',
            s['corpo'],
        ),
        tabela,
        Spacer(1, 0.4 * cm),
        Paragraph(
            '<b>Atenção:</b> a planilha deve ter uma linha de título mesclado no topo '
            '(ex: "CONTROLE DE PONTO") e uma linha de cabeçalho com os nomes das colunas. '
            'A última linha com "TOTAL" é ignorada automaticamente.',
            s['corpo'],
        ),
    ]


def secao_gui(s: dict) -> list:
    dados_componentes = [
        ['Componente', 'Widget customtkinter', 'Justificativa'],
        ['Janela principal', 'CTk (dark mode)', 'Tema escuro ativo por padrão; paleta da empresa (vermelho #C0391B sobre fundo #0f0f0f).'],
        ['Campos de texto', 'CTkEntry + tk.StringVar', 'StringVar separa modelo da visão; Entry moderno integrado ao tema dark.'],
        ['Botões de arquivo', 'CTkButton + filedialog', 'Diálogo nativo do Windows; botão ⋯ discreto ao lado do campo.'],
        ['Seletor de aba', 'CTkComboBox', 'Lista suspensa com dropdown estilizado no tema dark.'],
        ['Lista de funcionários', 'CTkScrollableFrame + CTkCheckBox', 'Frame scrollável com checkboxes nativos do customtkinter; todos marcados por padrão.'],
        ['Painel de prévia', 'CTkScrollableFrame + CTkLabel', 'Exibe a imagem PIL do recibo selecionado; atualiza em background thread.'],
        ['Navegação de prévia', 'CTkButton ← →', 'Navega entre os recibos selecionados sem regerar o PDF.'],
        ['Barra de progresso', 'CTkProgressBar (indeterminate)', 'Altura fina (3px), cor do accent — visualmente integrado ao design.'],
        ['Label de status', 'CTkLabel + tk.StringVar', 'Feedback textual sem caixas de diálogo; cor muda conforme estado (erro/sucesso).'],
        ['Botão principal', 'CTkButton', 'Fundo vermelho ACCENT; desabilitado durante geração para evitar cliques duplos.'],
        ['Diálogo de conclusão', 'messagebox.askyesno', 'Pergunta se deseja abrir o PDF — não abre automaticamente.'],
    ]

    tabela = mk_tabela(
        dados_componentes,
        [3.2 * cm, 3.8 * cm, 9.6 * cm],
        colors.HexColor('#C0391B'),
        s,
    )

    return [
        *divisor(),
        Paragraph('7. INTERFACE GRÁFICA (GUI) — IMPLEMENTAÇÃO', s['secao']),
        Paragraph(
            'A GUI usa <b>customtkinter</b> — um wrapper moderno sobre tkinter com dark mode nativo, '
            'widgets redesenhados e sistema de temas. O layout é dividido em dois painéis: '
            '<b>esquerdo</b> (controles, lista de funcionários) e <b>direito</b> (prévia do recibo). '
            'O comportamento CLI original é preservado: sem argumentos → abre a janela; '
            'com argumentos → modo CLI.',
            s['corpo'],
        ),
        *imagem_proporcional(
            'scheenshot_gui.png.png',
            LARGURA_UTIL,
            s,
            'Interface do Gerador de Recibos — painel de controles (esquerda) e prévia do recibo (direita).',
        ),

        Paragraph('Passo 1 — Escolha da biblioteca: customtkinter sobre tkinter puro', s['subsecao']),
        Paragraph(
            'Foram avaliadas as opções de biblioteca gráfica para Python:',
            s['corpo'],
        ),
        Paragraph(
            '• <b>customtkinter</b> ✔ — dark mode nativo; baseado em tkinter (sem dependências pesadas); '
            'widgets modernos; instalação simples via pip.',
            s['topico'],
        ),
        Paragraph(
            '• <b>tkinter puro</b> — visual datado; sem dark mode; checkboxes e scrollbars feias no Windows 11.',
            s['topico'],
        ),
        Paragraph(
            '• <b>PyQt / PySide6</b> ✘ — ~60 MB de instalação; licença LGPL; complexidade excessiva.',
            s['topico'],
        ),

        Paragraph('Passo 2 — Layout split com painéis esquerdo e direito', s['subsecao']),
        *bloco_codigo([
            'ctk.set_appearance_mode("dark")',
            'root = ctk.CTk()',
            'root.geometry("1100x680")',
            '',
            'main = ctk.CTkFrame(root, fg_color="transparent")',
            'left  = ctk.CTkFrame(main, width=460)   # controles',
            'right = ctk.CTkFrame(main)               # prévia',
        ], s),

        Paragraph('Passo 3 — Lista de funcionários com CTkScrollableFrame', s['subsecao']),
        Paragraph(
            'Cada funcionário é uma linha com CTkCheckBox (variável BooleanVar), label com nome '
            'e label com valor à direita. Todos marcados por padrão. Os pares '
            '<i>(var, nome, trace_id)</i> são guardados em <i>checks_vars</i> para filtrar '
            'na geração e para remover traces corretamente ao trocar de aba (ver seção de bugs).',
            s['corpo'],
        ),
        *bloco_codigo([
            'for func in funcionarios:',
            '    var = tk.BooleanVar(value=True)',
            '    trace_id = var.trace_add("write", _atualizar_summary)',
            '    checks_vars.append((var, func["nome"], trace_id))',
            '    cb = ctk.CTkCheckBox(row, variable=var, ...)',
        ], s),

        Paragraph('Passo 4 — Painel de prévia com renderização em background thread', s['subsecao']),
        Paragraph(
            'Ao selecionar ou desmarcar funcionários, a prévia do primeiro selecionado '
            'é renderizada em thread separada para não travar a UI. Um mecanismo de '
            '<b>token de cancelamento</b> garante que apenas o resultado mais recente seja aplicado.',
            s['corpo'],
        ),
        *bloco_codigo([
            'token = object()',
            '_preview_token[0] = token',
            '',
            'def _render():',
            '    pil_img = gerar_preview_pil(func, width=pw)',
            '    if _preview_token[0] is not token:',
            '        return  # resultado desatualizado — descarta',
            '    def _apply():',
            '        _clear_preview_image()   # limpa referência stale (ver seção de bugs)',
            '        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, ...)',
            '        prev_label.configure(image=ctk_img, text="")',
            '        prev_label._ctk_img_ref = ctk_img',
            '    root.after(0, _apply)',
            '',
            'threading.Thread(target=_render, daemon=True).start()',
        ], s),

        Paragraph('Passo 5 — Execução da geração em thread separada', s['subsecao']),
        *bloco_codigo([
            'def tarefa():',
            '    try:',
            '        gerar_pdf_de_lista(funcionarios_sel, pdf)',
            '        root.after(0, lambda: concluido(pdf))',
            '    except Exception as exc:',
            '        msg = str(exc)',
            '        root.after(0, lambda: erro(msg))',
            'threading.Thread(target=tarefa, daemon=True).start()',
        ], s),
        Paragraph(
            '<b>root.after(0, callback):</b> O customtkinter/tkinter não é thread-safe. '
            'Toda atualização de widget deve ocorrer na thread principal via <i>root.after</i>. '
            '<b>Captura da exceção antes do lambda:</b> em Python 3, a variável de um bloco '
            '<i>except</i> é deletada ao sair do bloco — capturar <i>msg = str(exc)</i> '
            'antes evita NameError no lambda.',
            s['corpo'],
        ),

        Paragraph('Passo 6 — Compatibilidade com o modo CLI', s['subsecao']),
        *bloco_codigo([
            'def main():',
            '    if len(sys.argv) < 2:',
            '        iniciar_gui()   # sem argumentos → abre a janela',
            '        return',
            '    # com argumentos → comportamento CLI original inalterado',
        ], s),

        Spacer(1, 0.4 * cm),
        Paragraph('Resumo dos componentes', s['subsecao']),
        tabela,
    ]


def secao_executavel(s: dict) -> list:
    dados_flags = [
        ['Flag / Opção', 'O que faz', 'Por que foi usada'],
        ['--onefile', 'Empacota tudo em um único .exe', 'O usuário recebe um só arquivo para copiar e usar — sem pastas auxiliares, sem risco de esquecer alguma DLL.'],
        ['--windowed', 'Suprime a janela de terminal (cmd)', 'Como o programa tem GUI, o terminal aberto junto seria distração visual e assustaria usuários não técnicos.'],
        ['--name "GeradorRecibos"', 'Define o nome do executável gerado', 'Sem esta flag o nome seria gerar_recibos.exe (nome do script). O nome amigável fica mais claro para o usuário final.'],
    ]

    tabela_flags = mk_tabela(
        dados_flags,
        [3.8 * cm, 4.2 * cm, 8.6 * cm],
        colors.HexColor('#1a237e'),
        s,
    )

    dados_ferramentas = [
        ['Ferramenta', 'Abordagem', 'Veredicto'],
        ['PyInstaller', 'Empacota o interpretador Python + dependências + script em um exe', '✔ Escolhido — maduro, amplamente documentado, suporte nativo a tkinter/pandas/reportlab.'],
        ['cx_Freeze', 'Gera uma pasta com exe + DLLs (não onefile por padrão)', '✘ Onefile mais trabalhoso; menos hooks automáticos para bibliotecas científicas.'],
        ['Nuitka', 'Compila Python para C e gera exe nativo', '✘ Requer compilador C instalado (MSVC/MinGW); build muito mais lento; complexidade desnecessária para este caso.'],
        ['py2exe', 'Clássico empacotador Windows', '✘ Abandonado para Python 3.9+; sem suporte ao Python 3.14 usado no projeto.'],
    ]

    tabela_ferramentas = mk_tabela(
        dados_ferramentas,
        [2.8 * cm, 5.5 * cm, 8.3 * cm],
        colors.HexColor('#37474f'),
        s,
    )

    return [
        *divisor(),
        Paragraph('8. GERAÇÃO DO EXECUTÁVEL WINDOWS (.exe) — PASSO A PASSO', s['secao']),
        Paragraph(
            'Para que o programa funcione em qualquer computador Windows sem precisar instalar '
            'o Python, ele foi convertido em um arquivo executável (.exe) usando a ferramenta '
            '<b>PyInstaller</b>. Esta seção documenta cada decisão tomada durante esse processo.',
            s['corpo'],
        ),

        # ── PASSO 1 ──
        Paragraph('Passo 1 — Escolha da ferramenta de empacotamento', s['subsecao']),
        Paragraph(
            'Existem quatro ferramentas principais para converter scripts Python em executáveis '
            'Windows. Todas foram avaliadas:',
            s['corpo'],
        ),
        tabela_ferramentas,
        Spacer(1, 0.3 * cm),
        Paragraph(
            '<b>Por que PyInstaller?</b> É a única opção com suporte testado e hooks automáticos '
            'para as três bibliotecas do projeto (pandas, reportlab, tkinter) no Python 3.14, sem '
            'exigir configuração manual adicional.',
            s['corpo'],
        ),

        # ── PASSO 2 ──
        Paragraph('Passo 2 — Instalação do PyInstaller', s['subsecao']),
        Paragraph(
            'O PyInstaller não vem com o Python — precisa ser instalado uma única vez na '
            'máquina de desenvolvimento:',
            s['corpo'],
        ),
        *bloco_codigo(['pip install pyinstaller'], s),
        Paragraph(
            '<b>Nota:</b> O PyInstaller é uma ferramenta de <i>desenvolvimento</i>. Ela '
            'não precisa estar instalada na máquina do usuário final — apenas na máquina '
            'onde o .exe é gerado.',
            s['corpo'],
        ),

        # ── PASSO 3 ──
        Paragraph('Passo 3 — Comando de geração do executável', s['subsecao']),
        Paragraph('O comando completo utilizado foi:', s['corpo']),
        *bloco_codigo([
            'python -m PyInstaller --onefile --windowed --name "GeradorRecibos" gerar_recibos.py',
        ], s),
        Paragraph('Detalhamento de cada flag:', s['corpo']),
        tabela_flags,
        Spacer(1, 0.3 * cm),
        Paragraph(
            '<b>Por que python -m PyInstaller e não pyinstaller direto?</b> O pip instalou '
            'o executável pyinstaller.exe em uma pasta fora do PATH do sistema. Usar '
            '<i>python -m PyInstaller</i> garante que o módulo correto seja chamado, '
            'independente de configuração de PATH.',
            s['corpo'],
        ),

        # ── PASSO 4 ──
        Paragraph('Passo 4 — O que acontece internamente durante o build', s['subsecao']),
        Paragraph(
            'O PyInstaller executa as seguintes etapas automaticamente:',
            s['corpo'],
        ),
        Paragraph(
            '<b>1. Análise de dependências:</b> Percorre todas as importações do script '
            '(<i>import pandas</i>, <i>import reportlab</i>, etc.) e mapeia recursivamente '
            'todos os módulos necessários, incluindo dependências de dependências.',
            s['topico'],
        ),
        Paragraph(
            '<b>2. Hooks automáticos:</b> Para bibliotecas complexas como pandas e reportlab, '
            'o PyInstaller aplica "hooks" — scripts que incluem arquivos de dados extras '
            'que a análise estática não detectaria (ex: fontes do reportlab, dados de fuso '
            'horário do pandas).',
            s['topico'],
        ),
        Paragraph(
            '<b>3. Empacotamento em PYZ:</b> Os módulos Python são compilados para bytecode '
            '(.pyc) e comprimidos em um arquivo <i>PYZ-00.pyz</i>.',
            s['topico'],
        ),
        Paragraph(
            '<b>4. Bootloader:</b> Um pequeno programa C (runw.exe para modo windowed) é '
            'usado como ponto de entrada. Ao ser executado, ele extrai os arquivos para uma '
            'pasta temporária e inicializa o interpretador Python embutido.',
            s['topico'],
        ),
        Paragraph(
            '<b>5. Empacotamento final:</b> Bootloader + PYZ + DLLs + dados são costurados '
            'em um único <i>GeradorRecibos.exe</i> (~40 MB).',
            s['topico'],
        ),

        # ── PASSO 5 ──
        Paragraph('Passo 5 — Estrutura de arquivos gerada', s['subsecao']),
        *bloco_codigo([
            'recibo_de_pagamento/',
            '├── build/                  ← arquivos intermediários do build (ignorar)',
            '│   └── GeradorRecibos/',
            '│       ├── Analysis-00.toc',
            '│       ├── PYZ-00.pyz',
            '│       ├── warn-GeradorRecibos.txt',
            '│       └── ...',
            '├── dist/                   ← pasta de saída',
            '│   └── GeradorRecibos.exe  ← ✔ este é o arquivo para distribuir',
            '└── GeradorRecibos.spec     ← receita de build gerada automaticamente',
        ], s),
        Paragraph(
            '<b>build/:</b> Arquivos temporários usados durante o processo. Podem ser '
            'apagados após o build sem problema — o PyInstaller os recria na próxima execução.',
            s['corpo'],
        ),
        Paragraph(
            '<b>dist/GeradorRecibos.exe:</b> O único arquivo necessário para distribuir. '
            'Pode ser copiado para qualquer computador Windows e executado com dois cliques.',
            s['corpo'],
        ),
        Paragraph(
            '<b>GeradorRecibos.spec:</b> Arquivo de configuração gerado automaticamente. '
            'Registra todas as opções usadas. Pode ser editado para builds avançados '
            '(adicionar ícone, incluir arquivos extras, etc.).',
            s['corpo'],
        ),

        # ── PASSO 6 ──
        Paragraph('Passo 6 — .gitignore: o que versionar e o que ignorar', s['subsecao']),
        Paragraph(
            'Os arquivos de build <b>não devem</b> ser versionados no git — são pesados, '
            'gerados automaticamente e específicos da máquina de desenvolvimento. '
            'O arquivo <i>.gitignore</i> foi atualizado com:',
            s['corpo'],
        ),
        *bloco_codigo([
            '# PyInstaller',
            'build/',
            'dist/',
            '*.spec',
        ], s),
        Paragraph(
            '<b>Por que ignorar o .spec?</b> O .spec é gerado a partir do comando com as '
            'flags e pode ser recriado a qualquer momento. Versionar arquivos gerados '
            'automaticamente cria ruído desnecessário no histórico git.',
            s['corpo'],
        ),

        # ── PASSO 7 ──
        Paragraph('Passo 7 — Como regenerar o executável após mudanças', s['subsecao']),
        Paragraph(
            'Sempre que o código do <i>gerar_recibos.py</i> for alterado, o executável '
            'precisa ser gerado novamente. O comando é sempre o mesmo:',
            s['corpo'],
        ),
        *bloco_codigo([
            'python -m PyInstaller --onefile --windowed --name "GeradorRecibos" gerar_recibos.py',
        ], s),
        Paragraph(
            'O PyInstaller detecta os arquivos de build anteriores e reutiliza o que '
            'não mudou, tornando builds subsequentes mais rápidos que o primeiro.',
            s['corpo'],
        ),

        # ── PASSO 8 ──
        Paragraph('Passo 8 — Como distribuir para outro computador', s['subsecao']),
        Paragraph(
            'O arquivo <b>dist\\GeradorRecibos.exe</b> é completamente autossuficiente. '
            'Para instalar em outro computador Windows:',
            s['corpo'],
        ),
        Paragraph(
            '1. Copie o arquivo <i>GeradorRecibos.exe</i> para o computador de destino '
            '(pen drive, e-mail, OneDrive, etc.).',
            s['topico'],
        ),
        Paragraph(
            '2. Coloque-o em qualquer pasta (ex: Área de Trabalho ou Documentos).',
            s['topico'],
        ),
        Paragraph(
            '3. Dê dois cliques para abrir. Na primeira execução, o Windows Defender pode '
            'exibir um aviso de "aplicativo desconhecido" — clique em <i>Mais informações</i> '
            'e depois em <i>Executar assim mesmo</i>. Isso acontece porque o executável não '
            'tem assinatura digital (certificado pago).',
            s['topico'],
        ),
        Paragraph(
            '4. Não é necessário instalar Python, pip ou qualquer dependência.',
            s['topico'],
        ),

        # ── AVISO IMPORTANTE ──
        Spacer(1, 0.3 * cm),
        Paragraph(
            '<b>Importante — compatibilidade de sistema operacional:</b> O executável gerado '
            'no Windows 64-bit roda <b>somente</b> em Windows 64-bit. Para rodar em Windows '
            '32-bit seria necessário gerar o .exe em uma máquina 32-bit. Para macOS ou Linux '
            'seria necessário gerar o executável nesses sistemas operacionais separadamente.',
            s['corpo'],
        ),

        # ── PASSO 9 ──
        Paragraph('Passo 9 — Ícone na barra de tarefas do Windows', s['subsecao']),
        Paragraph(
            'Após gerar o executável com <i>--icon</i>, o ícone aparece corretamente no '
            'Explorer e na Área de Trabalho, mas a barra de tarefas continuava exibindo '
            'o ícone genérico da pena do Tk. Isso acontece porque existem <b>dois ícones '
            'independentes</b> no Windows:',
            s['corpo'],
        ),
        Paragraph(
            '• <b>Ícone do arquivo .exe</b> — definido pela flag <i>--icon</i> do PyInstaller. '
            'Aparece no Explorer, Área de Trabalho e Iniciar. É estático, embutido no '
            'cabeçalho PE do executável.',
            s['topico'],
        ),
        Paragraph(
            '• <b>Ícone da janela em execução</b> — controlado pelo tkinter via '
            '<i>root.iconbitmap()</i>. É o que aparece na barra de tarefas e no canto '
            'superior esquerdo da janela enquanto o programa está aberto.',
            s['topico'],
        ),
        Paragraph(
            'Para corrigir, foram necessárias três mudanças:',
            s['corpo'],
        ),
        Paragraph('<b>1. Função resource_path()</b>', s['subsecao']),
        Paragraph(
            'Dentro de um executável gerado pelo PyInstaller (<i>--onefile</i>), os arquivos '
            'empacotados não ficam na pasta do .exe — são extraídos para uma pasta temporária '
            'em <i>C:\\Users\\...\\AppData\\Local\\Temp\\_MEIxxxxxx\\</i> cujo caminho fica em '
            '<i>sys._MEIPASS</i>. Ao rodar como script normal, esse atributo não existe.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def resource_path(filename: str) -> str:',
            '    """Caminho correto para recursos no .exe (PyInstaller) ou no script."""',
            '    base = getattr(sys, "_MEIPASS",',
            '                   os.path.dirname(os.path.abspath(__file__)))',
            '    return os.path.join(base, filename)',
        ], s),
        Paragraph(
            '<b>getattr(sys, "_MEIPASS", fallback):</b> Se o atributo não existir '
            '(execução como script), retorna o fallback — a pasta onde o .py está. '
            'Isso torna o código compatível com os dois modos sem if/else explícito.',
            s['corpo'],
        ),
        Paragraph('<b>2. root.iconbitmap() na inicialização da janela</b>', s['subsecao']),
        *bloco_codigo([
            'def iniciar_gui():',
            '    root = ctk.CTk()   # customtkinter — não tk.Tk()',
            '    root.title("Gerador de Recibos")',
            '',
            '    ico = resource_path("recibo.ico")',
            '    if os.path.exists(ico):',
            '        root.iconbitmap(ico)',
        ], s),
        Paragraph(
            '<b>Por que iconbitmap e não iconphoto?</b> No Windows, <i>iconbitmap()</i> com '
            'arquivo <i>.ico</i> é a forma mais confiável de definir o ícone da barra de '
            'tarefas. O <i>iconphoto()</i> aceita PNG mas pode apresentar inconsistências '
            'de renderização dependendo da versão do Windows e do Tcl/Tk.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que o if os.path.exists()?</b> Garante que, se o arquivo não for '
            'encontrado por qualquer motivo, o programa continua funcionando normalmente '
            'em vez de lançar uma exceção na inicialização.',
            s['corpo'],
        ),
        Paragraph('<b>3. --add-data no comando do PyInstaller</b>', s['subsecao']),
        Paragraph(
            'Sem esta flag, o <i>recibo.ico</i> não seria empacotado dentro do .exe e '
            '<i>resource_path()</i> nunca encontraria o arquivo em <i>sys._MEIPASS</i>:',
            s['corpo'],
        ),
        *bloco_codigo([
            'python -m PyInstaller --onefile --windowed \\',
            '    --name "GeradorRecibos" \\',
            '    --icon "recibo.ico" \\',
            '    --add-data "recibo.ico;." \\',
            '    gerar_recibos.py',
        ], s),
        Paragraph(
            'O formato <i>"recibo.ico;."</i> significa: inclua o arquivo <i>recibo.ico</i> '
            'e extraia-o na raiz (<i>.</i>) da pasta temporária <i>_MEIPASS</i>. '
            'O separador é <b>ponto-e-vírgula</b> no Windows (no Linux/macOS seria dois-pontos).',
            s['corpo'],
        ),
        Paragraph(
            '<b>Nota sobre cache de ícones do Windows:</b> Se após atualizar o .exe o ícone '
            'antigo ainda aparecer na barra de tarefas, é o cache de ícones do Windows. '
            'Solução: clique com o botão direito no ícone antigo na barra → '
            '<i>Desafixar da barra de tarefas</i> → abra o novo .exe novamente.',
            s['corpo'],
        ),
    ]


def secao_futuro(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('9. PRÓXIMOS PASSOS PREVISTOS', s['secao']),
        Paragraph(
            'O programa já conta com interface gráfica, seleção de aba, filtro de funcionários, '
            'ícone personalizado e executável Windows. '
            'As melhorias abaixo são sugestões para evoluções futuras.',
            s['corpo'],
        ),
        Paragraph(
            '• <b>Período da semana no recibo:</b> exibir o intervalo de datas da semana '
            '(ex: "04 a 09 de abril de 2025") em vez de apenas a data de geração.',
            s['topico'],
        ),
        Paragraph(
            '• <b>Personalização da empresa:</b> permitir alterar nome, CNPJ e endereço '
            'direto pela interface sem editar o código.',
            s['topico'],
        ),
        Paragraph(
            '• <b>CPF no recibo:</b> incluir uma coluna de CPF na planilha e imprimir o '
            'dado em cada recibo para maior validade jurídica.',
            s['topico'],
        ),
        Paragraph(
            '• <b>Numeração dos recibos:</b> adicionar número sequencial (ex: "Recibo nº 001/2025") '
            'para facilitar controle e arquivo.',
            s['topico'],
        ),
    ]


def secao_testes(s: dict) -> list:
    dados_classes = [
        ['Classe de teste', 'O que testa'],
        ['TestFmtValor', 'Formatação monetária brasileira (R$ 1.234,56, zeros, milhão, centavo mínimo)'],
        ['TestValorPorExtenso', 'Conversão de valores numéricos para texto em pt_BR, incluindo centavos e valores negativos'],
        ['TestFormatarData', 'Formato "5 de janeiro de 2025", cobertura dos 12 meses, dia sem zero à esquerda'],
        ['TestLerFuncionarios', 'Leitura da planilha xlsx: funcionários válidos, planilha vazia, total zero/negativo ignorado, linha TOTAL ignorada, arquivo inexistente'],
        ['TestGerarPdfDeLista', 'Geração do PDF: arquivo criado, tamanho mínimo, lista vazia lança ValueError, múltiplos funcionários, XML injection, tamanho cresce com volume'],
        ['TestGerarPreviewPil', 'Renderização da prévia PIL: tipo retornado, largura correta, caracteres especiais no nome, valor alto, thread safety com 8 threads simultâneas'],
        ['TestResourcePath', 'Localização de recursos: fora do PyInstaller (usa __file__), dentro do PyInstaller (usa sys._MEIPASS via monkeypatch)'],
    ]

    tabela = mk_tabela(
        dados_classes,
        [4.2 * cm, 12.4 * cm],
        colors.HexColor('#2e4057'),
        s,
    )

    return [
        *divisor(),
        Paragraph('10. SUITE DE TESTES (PYTEST)', s['secao']),
        Paragraph(
            'Todas as funções críticas do programa são cobertas por uma suite de testes '
            'automatizados usando <b>pytest</b>. Os testes garantem que mudanças futuras '
            'no código não quebrem o comportamento esperado.',
            s['corpo'],
        ),

        Paragraph('Executar os testes', s['subsecao']),
        *bloco_codigo([
            '# Instalar pytest (apenas uma vez)',
            'pip install pytest openpyxl',
            '',
            '# Rodar todos os testes',
            'python -m pytest test_gerar_recibos.py -v',
        ], s),
        Paragraph(
            '<b>Cobertura atual: 29 testes, todos passando.</b>',
            s['corpo'],
        ),

        Paragraph('Classes de teste', s['subsecao']),
        tabela,
        Spacer(1, 0.4 * cm),

        Paragraph('Estratégia de fixtures', s['subsecao']),
        Paragraph(
            'As fixtures do pytest criam planilhas <i>.xlsx</i> temporárias em <i>tmp_path</i> '
            '(pasta descartada automaticamente após cada teste) para cobrir três cenários:',
            s['corpo'],
        ),
        Paragraph('• <b>xlsx_simples</b> — 2 funcionários válidos + linha TOTAL para verificar leitura correta.', s['topico']),
        Paragraph('• <b>xlsx_vazia</b> — apenas cabeçalho, para verificar retorno de lista vazia.', s['topico']),
        Paragraph('• <b>xlsx_invalidos</b> — funcionários com total zero e negativo, para verificar filtro.', s['topico']),

        Paragraph('Thread safety da prévia', s['subsecao']),
        Paragraph(
            'O teste <i>test_thread_safety</i> dispara 8 threads simultâneas renderizando '
            'previews com <i>gerar_preview_pil</i>. Cada thread recebe um funcionário '
            'diferente e o resultado é verificado. A ausência de erros confirma que a '
            'função é safe para uso concorrente.',
            s['corpo'],
        ),
        *bloco_codigo([
            'def test_thread_safety(self):',
            '    results, errors = [], []',
            '    def render(i):',
            '        try:',
            '            img = gerar_preview_pil({...}, width=320)',
            '            results.append(img.size)',
            '        except Exception as exc:',
            '            errors.append(str(exc))',
            '    threads = [threading.Thread(target=render, args=(i,)) for i in range(8)]',
            '    for t in threads: t.start()',
            '    for t in threads: t.join()',
            '    assert errors == []',
        ], s),
    ]


def secao_logging(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('11. SISTEMA DE LOG PERSISTENTE', s['secao']),
        Paragraph(
            'O programa grava um log rotativo em arquivo para facilitar o diagnóstico '
            'de problemas sem acesso ao terminal — especialmente quando executado como '
            '<i>.exe</i> em modo windowed.',
            s['corpo'],
        ),

        Paragraph('Localização do arquivo de log', s['subsecao']),
        *bloco_codigo([
            r'%APPDATA%\GeradorRecibos\gerador.log',
            r'# Exemplo: C:\Users\cleit\AppData\Roaming\GeradorRecibos\gerador.log',
        ], s),

        Paragraph('Configuração do RotatingFileHandler', s['subsecao']),
        *bloco_codigo([
            'def setup_logging() -> str:',
            '    app_dir = os.path.join(os.environ["APPDATA"], "GeradorRecibos")',
            '    os.makedirs(app_dir, exist_ok=True)',
            '    log_path = os.path.join(app_dir, "gerador.log")',
            '    fh = logging.handlers.RotatingFileHandler(',
            '        log_path,',
            '        maxBytes=1_048_576,  # 1 MB por arquivo',
            '        backupCount=3,       # mantém gerador.log.1, .2, .3',
            '        encoding="utf-8",',
            '    )',
            '    fh.setFormatter(logging.Formatter(',
            '        "%(asctime)s %(levelname)-8s %(message)s",',
            '        datefmt="%Y-%m-%d %H:%M:%S",',
            '    ))',
            '    logging.getLogger().setLevel(logging.WARNING)  # root: suprime ruído',
            '    for name in ("gerar_recibos", "__main__"):',
            '        lg = logging.getLogger(name)',
            '        lg.setLevel(logging.DEBUG)',
            '        lg.addHandler(fh)',
        ], s),

        Paragraph('Decisões técnicas', s['subsecao']),
        Paragraph(
            '<b>Por que %APPDATA%?</b> Em Windows, aplicativos não devem gravar arquivos '
            'na pasta do executável — pode estar em Program Files (sem permissão de escrita). '
            'O <i>%APPDATA%</i> é sempre gravável pelo usuário atual.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que rotativo?</b> O programa pode ser usado semanalmente por anos. '
            'Um log sem rotação cresceria indefinidamente. Com 1 MB + 3 backups, o histórico '
            'total é de 4 MB — suficiente para diagnóstico sem consumo excessivo de disco.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que root em WARNING e loggers da app em DEBUG?</b> Pandas, Pillow e '
            'outras bibliotecas emitem mensagens internas de baixo interesse. Manter o root '
            'em WARNING suprime esse ruído. Os loggers <i>"gerar_recibos"</i> e '
            '<i>"__main__"</i> em DEBUG capturam tudo que importa para diagnóstico.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Por que dois nomes de logger?</b> O objeto '
            '<i>log = logging.getLogger(__name__)</i> recebe o nome <i>"gerar_recibos"</i> '
            'quando importado como módulo (pelos testes, por exemplo), mas <i>"__main__"</i> '
            'quando executado diretamente. Configurar ambos garante cobertura nos dois modos.',
            s['corpo'],
        ),

        Paragraph('Exemplo de saída no log', s['subsecao']),
        *bloco_codigo([
            '2026-04-19 06:52:39 INFO     GeradorRecibos iniciando',
            '2026-04-19 06:52:49 INFO     carregar_funcionarios: arquivo=\'...\' aba=\'Ponto 06-11.04.2026\'',
            '2026-04-19 06:52:49 INFO     carregar_funcionarios: 18 funcionario(s) carregados',
            '2026-04-19 07:04:22 INFO     carregar_funcionarios: 17 funcionario(s) carregados',
        ], s),
    ]


def secao_bugs_resolvidos(s: dict) -> list:
    return [
        *divisor(),
        Paragraph('12. BUGS RESOLVIDOS — DETALHES TÉCNICOS', s['secao']),
        Paragraph(
            'Dois bugs não triviais foram encontrados e corrigidos durante o desenvolvimento '
            'da interface gráfica. Ambos envolvem o comportamento interno do customtkinter '
            'e do tkinter — documentados aqui para referência futura.',
            s['corpo'],
        ),

        # ── BUG 1 ──
        Paragraph('Bug 1 — CTkLabel não limpa a imagem ao receber image=None', s['subsecao']),
        Paragraph(
            '<b>Sintoma:</b> Ao trocar de aba na planilha, o log registrava '
            '<i>TclError: image "pyimage2" doesn\'t exist</i> dentro de '
            '<i>prev_label.configure(image=None, text=\'...\')</i>.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Causa raiz:</b> O método <i>CTkLabel._update_image()</i> do customtkinter '
            'não chama <i>self._label.configure(image=\'\')</i> quando <i>self._image</i> '
            'passa a ser <i>None</i> — ele apenas atualiza o estado Python interno. '
            'O widget tkinter subjacente mantém a referência ao nome do <i>PhotoImage</i> '
            '(<i>"pyimage2"</i>, etc.). Quando o objeto Python <i>CTkImage</i> é coletado '
            'pelo GC, o <i>PhotoImage</i> é deletado do Tcl — mas o label ainda referencia '
            'o nome. O <i>configure</i> processa o parâmetro <i>text</i> antes do '
            '<i>image</i> (linha 204 vs 216 em <i>ctk_label.py</i>), causando o '
            '<i>TclError</i> antes mesmo de tentar limpar a imagem.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Fix aplicado:</b> helper <i>_clear_preview_image()</i> que limpa o widget '
            'tkinter interno diretamente via <i>prev_label._label.configure(image=\'\')</i> '
            '<b>antes</b> de liberar a referência Python, contornando o bug interno do customtkinter:',
            s['corpo'],
        ),
        *bloco_codigo([
            'def _clear_preview_image():',
            '    """CTkLabel._update_image() não limpa o widget tkinter quando image=None.',
            '    Limpar diretamente antes de liberar o CTkImage evita TclError."""',
            '    prev_label._ctk_img_ref = None',
            '    try:',
            "        prev_label._label.configure(image='')",
            '    except Exception:',
            '        pass',
        ], s),
        Paragraph(
            'A função é chamada em três pontos: em <i>_clear_scroll()</i> (troca de aba), '
            'em <i>_atualizar_preview()</i> quando não há funcionário selecionado, e '
            'em <i>_apply()</i> (callback da thread de renderização) antes de aplicar '
            'a nova imagem.',
            s['corpo'],
        ),

        # ── BUG 2 ──
        Paragraph('Bug 2 — Trace de BooleanVar causava TclError ao trocar de aba', s['subsecao']),
        Paragraph(
            '<b>Sintoma:</b> Ao trocar de aba, a lista de funcionários desaparecia '
            'ou ficava em branco mesmo com dados válidos na planilha. O log mostrava '
            'a abertura do arquivo mas sem a mensagem de funcionários carregados.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Causa raiz:</b> Em <i>_clear_scroll()</i>, todos os traces dos '
            '<i>BooleanVar</i> eram removidos antes de destruir os widgets. '
            'O <i>CTkCheckBox.destroy()</i> tentava remover seu próprio trace interno '
            'do mesmo <i>BooleanVar</i> — mas ele já havia sido removido. '
            'O <i>TclError</i> resultante era silenciado pelo tkinter, deixando '
            '<i>list_frame[0]</i> apontando para um frame destruído. '
            'Na próxima carga, novos widgets eram criados como filhos de um frame '
            'destruído — cascata de erros.',
            s['corpo'],
        ),
        Paragraph(
            '<b>Fix aplicado:</b> armazenar o ID exato de cada trace em uma 3-tupla '
            '<i>(var, nome, trace_id)</i> e remover <b>somente</b> o trace da aplicação '
            'pelo ID, preservando o trace interno do <i>CTkCheckBox</i>:',
            s['corpo'],
        ),
        *bloco_codigo([
            '# Ao criar o checkbox:',
            'trace_id = var.trace_add("write", _atualizar_summary)',
            'checks_vars.append((var, func["nome"], trace_id))',
            '',
            '# Em _clear_scroll() — remove apenas o nosso trace:',
            'for var, _nome, trace_id in checks_vars:',
            '    try:',
            '        var.trace_remove("write", trace_id)',
            '    except Exception:',
            '        pass',
            'checks_vars.clear()',
        ], s),
        Paragraph(
            'O <i>_make_list_frame()</i> também ganhou um <i>try/except</i> no '
            '<i>destroy()</i> para garantir que o novo frame seja sempre criado '
            'mesmo se a destruição do anterior falhar:',
            s['corpo'],
        ),
        *bloco_codigo([
            'def _make_list_frame():',
            '    try:',
            '        list_frame[0].destroy()',
            '    except Exception:',
            '        pass',
            '    list_frame[0] = ctk.CTkFrame(scroll, fg_color="transparent")',
            '    list_frame[0].pack(fill="x")',
        ], s),
    ]


# ---------------------------------------------------------------------------
# Geração do PDF
# ---------------------------------------------------------------------------

def gerar_documentacao():
    arquivo_pdf = (
        r'C:\Users\cleit\OneDrive\Documentos\recibo_de_pagamento'
        r'\documentacao_gerar_recibos.pdf'
    )

    doc = SimpleDocTemplate(
        arquivo_pdf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    s = criar_estilos()

    story = []
    story += secao_capa(s)
    story += secao_objetivo(s)
    story += secao_bibliotecas(s)
    story += secao_estrutura(s)
    story += secao_layout(s)
    story += secao_uso(s)
    story += secao_estrutura_planilha(s)
    story += secao_gui(s)
    story += secao_executavel(s)
    story += secao_futuro(s)
    story += secao_testes(s)
    story += secao_logging(s)
    story += secao_bugs_resolvidos(s)
    story += divisor()
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph('Fim da documentação.', s['rodape']))

    doc.build(story)
    print(f'Documentação gerada: {arquivo_pdf}')


if __name__ == '__main__':
    gerar_documentacao()
