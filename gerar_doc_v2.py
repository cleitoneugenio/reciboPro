"""
Gerador de documentação PDF para reciboPro V2.
Replica o estilo visual da documentação V1 (Helvetica + Courier, layout clean).
"""

import re
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import (
    HexColor, black, white, Color
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, HRFlowable, KeepTogether, PageBreak,
    Image as RLImage,
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib import colors

# ─── Paleta ────────────────────────────────────────────────────────────────
C_TITLE        = HexColor('#0A1628')   # azul-noite para título principal
C_H2           = HexColor('#0A1628')   # seções principais
C_H3           = HexColor('#1A3A6B')   # sub-seções
C_CODE_BG      = HexColor('#F4F6FA')   # fundo bloco de código
C_CODE_TEXT    = HexColor('#1A2840')   # texto de código
C_TABLE_HEADER = HexColor('#1A3A6B')   # cabeçalho de tabela
C_TABLE_ROW1   = HexColor('#FFFFFF')   # linha ímpar
C_TABLE_ROW2   = HexColor('#F0F4FA')   # linha par
C_TABLE_GRID   = HexColor('#C8D8EF')   # grade da tabela
C_HR           = HexColor('#C8D8EF')   # linha horizontal
C_MUTED        = HexColor('#5A7090')   # texto secundário
C_CALLOUT_BG   = HexColor('#EEF4FF')   # fundo "Por que assim?"
C_CALLOUT_BAR  = HexColor('#1A3A6B')   # barra lateral callout
C_BULLET       = HexColor('#1A3A6B')

PAGE_W, PAGE_H = A4
MARGIN_H = 2.0 * cm
MARGIN_V = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN_H

# ─── Estilos ───────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {
        'cover_title': ParagraphStyle(
            'cover_title',
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=34,
            textColor=C_TITLE,
            spaceAfter=6,
            alignment=TA_CENTER,
        ),
        'cover_sub': ParagraphStyle(
            'cover_sub',
            fontName='Helvetica',
            fontSize=14,
            leading=18,
            textColor=C_MUTED,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        'cover_meta': ParagraphStyle(
            'cover_meta',
            fontName='Helvetica',
            fontSize=10,
            leading=16,
            textColor=C_MUTED,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        'cover_desc': ParagraphStyle(
            'cover_desc',
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=HexColor('#3A4A60'),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        'h2': ParagraphStyle(
            'h2',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=C_H2,
            spaceBefore=18,
            spaceAfter=6,
            borderPadding=(0, 0, 4, 0),
        ),
        'h3': ParagraphStyle(
            'h3',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=C_H3,
            spaceBefore=12,
            spaceAfter=4,
        ),
        'body': ParagraphStyle(
            'body',
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=HexColor('#1A2840'),
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        'bullet': ParagraphStyle(
            'bullet',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=HexColor('#1A2840'),
            spaceAfter=3,
            leftIndent=16,
            bulletIndent=4,
            bulletFontName='Helvetica-Bold',
            bulletFontSize=10,
            bulletColor=C_BULLET,
        ),
        'code': ParagraphStyle(
            'code',
            fontName='Courier',
            fontSize=8.5,
            leading=13,
            textColor=C_CODE_TEXT,
            backColor=C_CODE_BG,
            spaceAfter=0,
        ),
        'table_header': ParagraphStyle(
            'table_header',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=white,
            alignment=TA_CENTER,
        ),
        'table_cell': ParagraphStyle(
            'table_cell',
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=HexColor('#1A2840'),
        ),
        'callout': ParagraphStyle(
            'callout',
            fontName='Helvetica-Oblique',
            fontSize=9.5,
            leading=14,
            textColor=HexColor('#1A3A6B'),
            leftIndent=12,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
        ),
        'footer': ParagraphStyle(
            'footer',
            fontName='Helvetica',
            fontSize=8,
            textColor=C_MUTED,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ─── Flowable: bloco de código com fundo ──────────────────────────────────
class CodeBlock(Flowable):
    def __init__(self, text, width=CONTENT_W):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.pad = 10
        self._lines = text.split('\n')

    def wrap(self, available_width, available_height):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        self.width = available_width
        line_h = 13
        self.height = len(self._lines) * line_h + self.pad * 2
        return self.width, self.height

    def draw(self):
        c = self.canv
        pad = self.pad
        line_h = 13

        # Background
        c.setFillColor(C_CODE_BG)
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)

        # Left accent bar
        c.setFillColor(C_TABLE_HEADER)
        c.rect(0, 0, 3, self.height, fill=1, stroke=0)

        # Text
        c.setFont('Courier', 8.5)
        c.setFillColor(C_CODE_TEXT)
        y = self.height - pad - line_h + 3
        for line in self._lines:
            c.drawString(pad + 4, y, line)
            y -= line_h


# ─── Flowable: bloco callout "Por que assim?" ─────────────────────────────
class CalloutBlock(Flowable):
    def __init__(self, text, width=CONTENT_W):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self._para = None

    def wrap(self, available_width, available_height):
        self.width = available_width
        style = ParagraphStyle(
            'cb_inner',
            fontName='Helvetica-Oblique',
            fontSize=9.5,
            leading=14,
            textColor=HexColor('#1A3A6B'),
            leftIndent=0,
        )
        inner_w = self.width - 24  # bar(4) + gap(8) + padding(12)
        self._para = Paragraph(self.text, style)
        w, h = self._para.wrap(inner_w, available_height)
        self.height = h + 16
        return self.width, self.height

    def draw(self):
        c = self.canv
        pad = 8
        # Background
        c.setFillColor(C_CALLOUT_BG)
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        # Left bar
        c.setFillColor(C_CALLOUT_BAR)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        # Draw paragraph
        self._para.drawOn(c, 4 + pad, pad)


# ─── Cabeçalho e rodapé de página ─────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4

    if doc.page == 1:
        canvas.restoreState()
        return

    # Header line + text
    canvas.setStrokeColor(C_HR)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_H, h - MARGIN_V + 6, w - MARGIN_H, h - MARGIN_V + 6)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN_H, h - MARGIN_V + 10, 'reciboPro V2 — Documentação Técnica')
    canvas.drawRightString(w - MARGIN_H, h - MARGIN_V + 10, 'HigherMind')

    # Footer line + page number
    canvas.setStrokeColor(C_HR)
    canvas.line(MARGIN_H, MARGIN_V - 6, w - MARGIN_H, MARGIN_V - 6)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawCentredString(w / 2, MARGIN_V - 18, f'Página {doc.page}')

    canvas.restoreState()


# ─── Parser de Markdown simplificado ──────────────────────────────────────
def inline_markup(text):
    """Converte **bold**, *italic*, `code` em tags RML."""
    # Escape XML special chars FIRST (except what we'll insert)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # *italic* (not inside bold)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # `code`
    text = re.sub(r'`(.+?)`', r'<font name="Courier" size="9">\1</font>', text)
    return text


def parse_markdown(md_text, styles, img_dir):
    """Parse markdown into a list of ReportLab flowables."""
    story = []
    lines = md_text.split('\n')
    i = 0
    in_code = False
    code_lines = []
    code_lang = ''

    def flush_code():
        nonlocal code_lines, code_lang
        if code_lines:
            full_code = '\n'.join(code_lines)
            story.append(Spacer(1, 4))
            story.append(CodeBlock(full_code))
            story.append(Spacer(1, 8))
        code_lines = []
        code_lang = ''

    table_rows = []
    in_table = False

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        data = []
        col_count = max(len(r) for r in table_rows)
        for row in table_rows:
            padded = row + [''] * (col_count - len(row))
            data.append([Paragraph(inline_markup(c), styles['table_cell']) for c in padded])

        if not data:
            return

        # Header row uses special style
        header_cells = [Paragraph(inline_markup(c.get_platypus_text() if hasattr(c, 'get_platypus_text') else ''), styles['table_header']) for c in data[0]]
        # Rebuild header with table_header style
        header_row = []
        for row in [table_rows[0]]:
            for cell in row:
                header_row.append(Paragraph(inline_markup(cell), styles['table_header']))
        while len(header_row) < col_count:
            header_row.append(Paragraph('', styles['table_header']))

        data[0] = header_row

        col_w = CONTENT_W / col_count
        col_widths = [col_w] * col_count

        t = Table(data, colWidths=col_widths, repeatRows=1)
        ts = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_TABLE_ROW1, C_TABLE_ROW2]),
            ('GRID', (0, 0), (-1, -1), 0.5, C_TABLE_GRID),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        t.setStyle(ts)
        story.append(Spacer(1, 6))
        story.append(t)
        story.append(Spacer(1, 8))
        table_rows.clear()

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.startswith('```'):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip()
                code_lines = []
            else:
                in_code = False
                flush_table()
                flush_code()
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Table row
        if line.startswith('|'):
            parts = [c.strip() for c in line.split('|')[1:-1]]
            # Skip separator row (---|--- pattern)
            if all(re.match(r'^[-:]+$', p) for p in parts if p):
                i += 1
                continue
            in_table = True
            table_rows.append(parts)
            i += 1
            continue
        else:
            if in_table:
                flush_table()
                in_table = False

        # Horizontal rule
        if re.match(r'^---+\s*$', line):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width='100%', thickness=0.5, color=C_HR))
            story.append(Spacer(1, 8))
            i += 1
            continue

        # Image: ![alt](path)
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line.strip())
        if img_match:
            alt = img_match.group(1)
            src = img_match.group(2)
            full_path = os.path.join(img_dir, src)
            if os.path.exists(full_path):
                try:
                    img = RLImage(full_path, width=CONTENT_W * 0.85, height=None)
                    img.hAlign = 'CENTER'
                    story.append(Spacer(1, 8))
                    story.append(img)
                    story.append(Spacer(1, 4))
                except Exception:
                    pass
            i += 1
            continue

        # Italic-only line (image caption: *text*)
        cap_match = re.match(r'^\*([^*]+)\*$', line.strip())
        if cap_match:
            cap_style = ParagraphStyle(
                'caption', fontName='Helvetica-Oblique', fontSize=8.5,
                textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=8,
            )
            story.append(Paragraph(cap_match.group(1), cap_style))
            i += 1
            continue

        # H1 — cover title (skip in body, already handled)
        if line.startswith('# ') and not line.startswith('## '):
            # Only first H1 is the cover — handled separately
            i += 1
            continue

        # H2
        if line.startswith('## '):
            text = line[3:].strip()
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width='100%', thickness=1.5, color=C_H2, spaceAfter=4))
            story.append(Paragraph(text, styles['h2']))
            i += 1
            continue

        # H3
        if line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, styles['h3']))
            i += 1
            continue

        # Bullet list
        bullet_match = re.match(r'^[-*] (.+)', line)
        if bullet_match:
            text = inline_markup(bullet_match.group(1))
            story.append(Paragraph(f'<bullet>&bull;</bullet>{text}', styles['bullet']))
            i += 1
            continue

        # Numbered list
        num_match = re.match(r'^\d+\. (.+)', line)
        if num_match:
            text = inline_markup(num_match.group(1))
            story.append(Paragraph(f'<bullet>&bull;</bullet>{text}', styles['bullet']))
            i += 1
            continue

        # Empty line
        if not line.strip():
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Regular paragraph
        text = inline_markup(line.strip())
        if text:
            story.append(Paragraph(text, styles['body']))

        i += 1

    flush_table()
    if in_code:
        flush_code()

    return story


# ─── Capa ──────────────────────────────────────────────────────────────────
def build_cover(styles, icon_path):
    cover = []
    cover.append(Spacer(1, 2.5 * cm))

    # Icon
    if os.path.exists(icon_path):
        try:
            icon = RLImage(icon_path, width=3.5 * cm, height=3.5 * cm)
            icon.hAlign = 'CENTER'
            cover.append(icon)
            cover.append(Spacer(1, 0.6 * cm))
        except Exception:
            pass

    cover.append(Paragraph('DOCUMENTAÇÃO TÉCNICA', styles['cover_title']))
    cover.append(Spacer(1, 0.2 * cm))
    cover.append(Paragraph('reciboPro V2 — Gerador de Recibos de Prestação de Serviço', styles['cover_sub']))
    cover.append(Spacer(1, 1.0 * cm))

    meta_lines = [
        '<b>Arquivo principal:</b> src/ (monorepo Electron)',
        '<b>Linguagem:</b> TypeScript 5.7 (strict mode)',
        '<b>Runtime:</b> Electron 34.5.8 + React 19',
        '<b>Build tool:</b> electron-vite 3 + electron-builder 25',
        '<b>Produzido por:</b> HigherMind',
    ]
    for line in meta_lines:
        cover.append(Paragraph(line, styles['cover_meta']))

    cover.append(Spacer(1, 0.8 * cm))
    cover.append(HRFlowable(width='60%', thickness=1, color=C_HR, hAlign='CENTER'))
    cover.append(Spacer(1, 0.8 * cm))

    cover.append(Paragraph(
        'Este documento explica passo a passo como a V2 do programa foi construída, '
        'o motivo de cada escolha técnica, como cada módulo funciona, '
        'bugs encontrados e como utilizá-lo no dia a dia.',
        styles['cover_desc']
    ))

    cover.append(PageBreak())
    return cover


# ─── Main ──────────────────────────────────────────────────────────────────
def main():
    base_dir = r'c:\Users\cleit\OneDrive\Documentos\reciboPro'
    md_path  = os.path.join(base_dir, 'documentacao_recibopro_v2.md')
    out_path = os.path.join(base_dir, 'documentacao_recibopro_v2.pdf')
    icon_path = os.path.join(base_dir, 'recibo.png')

    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()

    # Skip cover block (everything before the first ## section)
    first_h2 = md_text.find('\n## ')
    if first_h2 != -1:
        md_text = md_text[first_h2 + 1:]

    styles = build_styles()

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_V,
        bottomMargin=MARGIN_V,
        title='Documentação Técnica — reciboPro V2',
        author='HigherMind',
    )

    story = build_cover(styles, icon_path)
    story += parse_markdown(md_text, styles, base_dir)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF gerado: {out_path}')


if __name__ == '__main__':
    main()
