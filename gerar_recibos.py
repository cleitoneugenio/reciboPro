#!/usr/bin/env python3
"""
Gerador de Recibos de Prestação de Serviço
Uso: python gerar_recibos.py <arquivo.xlsx> [saida.pdf]
"""

import logging
import logging.handlers
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

import customtkinter as ctk

import pandas as pd
from num2words import num2words
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

log = logging.getLogger(__name__)


def setup_logging() -> str:
    """Configura logging para arquivo rotativo em %APPDATA%/GeradorRecibos/.

    Retorna o caminho do arquivo de log.
    """
    app_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GeradorRecibos')
    os.makedirs(app_dir, exist_ok=True)
    log_path = os.path.join(app_dir, 'gerador.log')

    fmt = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Arquivo rotativo: máx 1 MB, mantém 3 arquivos anteriores
    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_048_576, backupCount=3, encoding='utf-8'
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Root logger em WARNING — suprime ruído de bibliotecas (Pillow, pandas, etc.)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(fh)

    # Loggers da aplicação em DEBUG — cobre tanto import quanto execução direta
    for name in ('gerar_recibos', '__main__'):
        logging.getLogger(name).setLevel(logging.DEBUG)

    # Console — apenas quando há terminal (desenvolvimento / CLI)
    if sys.stderr and sys.stderr.isatty():
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        root_logger.addHandler(ch)

    return log_path


def fmt_valor(valor: float) -> str:
    """Formata um valor float para o padrão monetário brasileiro (R$ 1.234,56)."""
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def valor_por_extenso(valor: float) -> str:
    reais = int(valor)
    centavos = round((valor - reais) * 100)
    extenso = num2words(reais, lang='pt_BR') + ' reais'
    if centavos > 0:
        extenso += ' e ' + num2words(centavos, lang='pt_BR') + ' centavos'
    return f'{fmt_valor(valor)} ({extenso})'


def formatar_data(data: datetime) -> str:
    meses = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
    ]
    return f'{data.day} de {meses[data.month - 1]} de {data.year}'


def ler_funcionarios(arquivo: str, sheet_name=0) -> list:
    df = pd.read_excel(arquivo, sheet_name=sheet_name, header=0)

    funcionarios = []
    for _, row in df.iterrows():
        # Col 0 = número do funcionário; deve ser inteiro positivo
        try:
            int(row.iloc[0])
        except (ValueError, TypeError):
            continue  # pula cabeçalho e linha TOTAL

        nome = str(row.iloc[1]).strip()
        if not nome or nome.lower() == 'nan':
            continue

        try:
            total = float(row.iloc[10])
        except (ValueError, TypeError):
            continue

        if total <= 0:
            continue

        funcionarios.append({'nome': nome, 'total': total})

    return funcionarios


def montar_recibo(nome: str, total: float, data_str: str, styles: dict) -> list:
    valor_str = valor_por_extenso(total)

    corpo_texto = (
        'Recebi da empresa <b>GF MUNIZ ARTEFACTOS DE CERAMICA EIRELI</b>, pessoa jurídica de '
        'direito privado, inscrita no CNPJ sob o n 12.509.424/0001-65, com sede na cidade de '
        'Bela Cruz - CE ROD CE 179 - KM 12 - S/N - Zona Rural, a quantia de '
        f'<b>{valor_str}</b>. '
        f'Referente a serviço de diárias no dia {data_str}. '
        'dando-lhe por este recibo a devida quitação.'
    )

    return [
        Paragraph(
            '<u><b>RECIBO DE PRESTAÇÃO DE SERVIÇO</b></u>',
            styles['titulo'],
        ),
        Spacer(1, 0.5 * cm),
        Paragraph(corpo_texto, styles['corpo']),
        Spacer(1, 0.4 * cm),
        Paragraph(f'Bela Cruz, {data_str}.', styles['corpo']),
        Spacer(1, 1.8 * cm),
        HRFlowable(width='55%', thickness=1, color=colors.black, hAlign='CENTER'),
        Spacer(1, 0.25 * cm),
        Paragraph(xml_escape(nome), styles['assinatura']),
    ]


def gerar_pdf_de_lista(funcionarios: list, arquivo_pdf: str) -> None:
    """Gera o PDF a partir de uma lista já carregada (e opcionalmente filtrada) de funcionários."""
    if not funcionarios:
        raise ValueError('Nenhum funcionário selecionado para gerar o PDF.')

    hoje = datetime.today()
    data_str = formatar_data(hoje)

    doc = SimpleDocTemplate(
        arquivo_pdf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = {
        'titulo': ParagraphStyle(
            'titulo',
            fontName='Helvetica-Bold',
            fontSize=13,
            alignment=TA_CENTER,
        ),
        'corpo': ParagraphStyle(
            'corpo',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_JUSTIFY,
            leading=15,
        ),
        'assinatura': ParagraphStyle(
            'assinatura',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
        ),
    }

    story = []

    for i, func in enumerate(funcionarios):
        recibo = montar_recibo(func['nome'], func['total'], data_str, styles)
        story.append(KeepTogether(recibo))

        if i < len(funcionarios) - 1:
            story.append(Spacer(1, 0.5 * cm))
            story.append(
                HRFlowable(
                    width='100%',
                    thickness=0.5,
                    color=colors.grey,
                    dash=(6, 4),
                    hAlign='CENTER',
                )
            )
            story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    log.info('PDF gerado: %s (%d recibos)', arquivo_pdf, len(funcionarios))


def gerar_pdf(arquivo_xlsx: str, arquivo_pdf: str) -> None:
    funcionarios = ler_funcionarios(arquivo_xlsx)
    if not funcionarios:
        log.warning('Nenhum funcionário encontrado na planilha: %s', arquivo_xlsx)
        sys.exit(1)
    gerar_pdf_de_lista(funcionarios, arquivo_pdf)


def gerar_preview_pil(funcionario: dict, width: int = 420):
    """Renderiza o recibo como imagem PIL — usado no painel de preview da GUI."""
    from PIL import Image, ImageDraw, ImageFont

    # ── Referência exata do PDF ───────────────────────────────────────────────
    # A4: 595.28pt × 841.89pt | margens: 2cm=56.69pt esq/dir, 1.5cm=42.52pt cima/baixo
    # Largura de conteúdo: 595.28 - 2×56.69 = 481.9pt
    PDF_CW_PT   = 481.9
    scale       = width / PDF_CW_PT   # px por pt

    # Tamanhos de fonte — idênticos ao PDF, escalados
    sz_title    = max(6, round(13 * scale))
    sz_body     = max(5, round(10 * scale))

    # Espaçadores — convertidos dos Spacer() do PDF (cm → pt: 1cm=28.35pt)
    sp_after_title  = max(2, round(0.5  * 28.35 * scale))   # Spacer(1, 0.5*cm)
    sp_after_corpo  = max(2, round(0.4  * 28.35 * scale))   # Spacer(1, 0.4*cm)
    sp_before_sig   = max(3, round(1.8  * 28.35 * scale))   # Spacer(1, 1.8*cm)
    sp_after_line   = max(1, round(0.25 * 28.35 * scale))   # Spacer(1, 0.25*cm)
    leading         = max(5, round(15   * scale))            # leading=15 no ParagraphStyle

    # Margem visual mínima em volta do bloco
    PAD   = max(8, round(8 * scale))
    cw    = width - 2 * PAD
    H_EST = int(width * 2)

    img  = Image.new('RGB', (width, H_EST), '#ffffff')
    draw = ImageDraw.Draw(img)

    C_BLACK = (22, 22, 22)

    arial   = 'C:/Windows/Fonts/arial.ttf'
    arialbd = 'C:/Windows/Fonts/arialbd.ttf'

    def _font(path, size):
        try:
            return ImageFont.truetype(path, size=max(1, size))
        except OSError:
            log.warning('Fonte não encontrada: %s — usando padrão', path)
            return ImageFont.load_default()

    f_title = _font(arialbd, sz_title)
    f_body  = _font(arial,   sz_body)

    def _tw(text, font):
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0]

    def _th(font):
        bb = draw.textbbox((0, 0), 'Ag', font=font)
        return bb[3] - bb[1]

    def _wrap_px(text, font, max_px):
        words, lines, lwords, lw = text.split(), [], [], 0
        sp = _tw(' ', font)
        for word in words:
            ww = _tw(word, font)
            if lwords and lw + sp + ww > max_px:
                lines.append(' '.join(lwords))
                lwords, lw = [word], ww
            else:
                lw = (lw + sp + ww) if lwords else ww
                lwords.append(word)
        if lwords:
            lines.append(' '.join(lwords))
        return lines

    y = PAD

    # Título — centralizado, negrito, sublinhado (TA_CENTER + <u><b> do PDF)
    titulo = 'RECIBO DE PRESTAÇÃO DE SERVIÇO'
    tw_t   = _tw(titulo, f_title)
    tx     = PAD + (cw - tw_t) // 2
    draw.text((tx, y), titulo, font=f_title, fill=C_BLACK)
    th_t = _th(f_title)
    draw.line([(tx, y + th_t + 1), (tx + tw_t, y + th_t + 1)], fill=C_BLACK, width=1)
    y += th_t + sp_after_title

    # Corpo — TA_JUSTIFY (aproximado com alinhamento à esquerda no PIL)
    valor_str = valor_por_extenso(funcionario['total'])
    data_str  = formatar_data(datetime.today())
    corpo = (
        f'Recebi da empresa GF MUNIZ ARTEFACTOS DE CERAMICA EIRELI, pessoa jurídica '
        f'de direito privado, inscrita no CNPJ sob o n 12.509.424/0001-65, com sede '
        f'na cidade de Bela Cruz - CE ROD CE 179 - KM 12 - S/N - Zona Rural, a '
        f'quantia de {valor_str}. Referente a serviço de diárias no dia {data_str}. '
        f'Dando-lhe por este recibo a devida quitação.'
    )
    for line in _wrap_px(corpo, f_body, cw):
        draw.text((PAD, y), line, font=f_body, fill=C_BLACK)
        y += leading

    y += sp_after_corpo

    # Data — TA_JUSTIFY (alinhado à esquerda)
    draw.text((PAD, y), f'Bela Cruz, {data_str}.', font=f_body, fill=C_BLACK)
    y += leading + sp_before_sig

    # Linha de assinatura — HRFlowable width='55%', hAlign='CENTER'
    sig_w = round(cw * 0.55)
    sig_x = PAD + (cw - sig_w) // 2
    draw.line([(sig_x, y), (sig_x + sig_w, y)], fill=C_BLACK, width=1)
    y += sp_after_line

    # Nome — TA_CENTER
    nome = funcionario['nome']
    nw   = _tw(nome, f_body)
    draw.text((PAD + (cw - nw) // 2, y), nome, font=f_body, fill=C_BLACK)
    y += _th(f_body) + PAD

    return img.crop((0, 0, width, min(y, H_EST)))


def resource_path(filename: str) -> str:
    """Retorna o caminho correto para recursos dentro do .exe (PyInstaller) ou do script."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def iniciar_gui():
    log.info('GeradorRecibos iniciando')
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('dark-blue')

    root = ctk.CTk()
    root.title('Gerador de Recibos')
    root.geometry('1100x680')
    root.minsize(960, 580)

    ico = resource_path('recibo.ico')
    if os.path.exists(ico):
        root.iconbitmap(ico)

    # ── Paleta ──────────────────────────────────────────────────────────────
    BG       = '#0f0f0f'
    SURFACE  = '#1a1a1a'
    SURFACE2 = '#242424'
    BORDER   = '#2e2e2e'
    TEXT     = '#f1f1f1'
    DIM3     = '#4b5563'   # disabled, placeholder
    DIM2     = '#6b7280'   # metadados, labels secundários
    DIM1     = '#9ca3af'   # labels de seção uppercase
    ACCENT   = '#C0391B'
    ACCENT_H = '#9B2E15'
    ERR      = '#f97316'

    root.configure(fg_color=BG)

    F_LABEL   = ctk.CTkFont('Segoe UI', 11)
    F_BODY    = ctk.CTkFont('Segoe UI', 12)
    F_SECTION = ctk.CTkFont('Segoe UI', 9)
    F_BUTTON  = ctk.CTkFont('Segoe UI', 13, 'bold')

    # ── Container principal (split horizontal) ──────────────────────────────
    main = ctk.CTkFrame(root, fg_color='transparent')
    main.pack(fill='both', expand=True, padx=0, pady=0)

    # Painel esquerdo — controles
    left = ctk.CTkFrame(main, fg_color='transparent', width=460)
    left.pack(side='left', fill='both', expand=False, padx=(28, 0), pady=24)
    left.pack_propagate(False)

    # Divisor vertical
    ctk.CTkFrame(main, fg_color=BORDER, width=1).pack(
        side='left', fill='y', padx=16, pady=24)

    # Painel direito — preview
    right = ctk.CTkFrame(main, fg_color='transparent')
    right.pack(side='left', fill='both', expand=True, padx=(0, 28), pady=24)

    # ── Header — logo ────────────────────────────────────────────────────────
    logo_path = resource_path('logo_forte_telha.png')
    if os.path.exists(logo_path):
        from PIL import Image as PilImage
        pil_logo = PilImage.open(logo_path).convert('RGBA')
        logo_h = 72
        logo_w = int(pil_logo.width * logo_h / pil_logo.height)
        ctk_logo = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo,
                                 size=(logo_w, logo_h))
        ctk.CTkLabel(left, image=ctk_logo, text='', anchor='center').pack(
            fill='x', pady=(0, 20))
    else:
        ctk.CTkLabel(left, text='FORTE TELHA', font=ctk.CTkFont('Segoe UI', 22, 'bold'),
                     text_color=ACCENT, anchor='w').pack(fill='x')
        ctk.CTkLabel(left, text='INDÚSTRIA DE CERÂMICA',
                     font=F_LABEL, text_color=DIM2, anchor='w').pack(fill='x', pady=(2, 16))

    # ── Inputs — micro-labels empilhados ────────────────────────────────────
    inp = ctk.CTkFrame(left, fg_color='transparent')
    inp.pack(fill='x', pady=(0, 16))

    def _micro_label(parent, text):
        ctk.CTkLabel(parent, text=text, font=F_SECTION,
                     text_color=DIM3, anchor='w').pack(fill='x', pady=(0, 3))

    def _input_row(parent):
        f = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=6,
                         border_width=1, border_color='#3d3d3d', height=36)
        f.pack(fill='x', pady=(0, 10))
        f.pack_propagate(False)
        return f

    def _browse_btn(parent):
        return ctk.CTkButton(parent, text='⋯', width=36, height=36,
                             fg_color='transparent', hover_color=SURFACE2,
                             text_color=DIM2, border_width=0,
                             font=ctk.CTkFont('Segoe UI', 13), corner_radius=6)

    # Planilha
    _micro_label(inp, 'PLANILHA')
    xlsx_wrap = _input_row(inp)
    var_xlsx = tk.StringVar()
    ctk.CTkEntry(xlsx_wrap, textvariable=var_xlsx, height=34,
                 fg_color='transparent', border_width=0,
                 text_color=TEXT, font=F_BODY).pack(
        side='left', fill='both', expand=True, padx=(10, 0))
    btn_xlsx = _browse_btn(xlsx_wrap)
    btn_xlsx.pack(side='right')

    # Aba
    _micro_label(inp, 'ABA')
    var_aba = tk.StringVar()
    combo_aba = ctk.CTkComboBox(inp, variable=var_aba, values=[], state='disabled',
                                height=36, fg_color=SURFACE, border_color='#3d3d3d',
                                button_color=SURFACE2, button_hover_color=BORDER,
                                dropdown_fg_color=SURFACE2,
                                dropdown_hover_color=BORDER,
                                text_color=TEXT, font=F_BODY)
    combo_aba.pack(fill='x', pady=(0, 10))

    # PDF saída
    _micro_label(inp, 'PDF DE SAÍDA')
    pdf_wrap = _input_row(inp)
    var_pdf = tk.StringVar()
    ctk.CTkEntry(pdf_wrap, textvariable=var_pdf, height=34,
                 fg_color='transparent', border_width=0,
                 text_color=TEXT, font=F_BODY).pack(
        side='left', fill='both', expand=True, padx=(10, 0))
    btn_pdf = _browse_btn(pdf_wrap)
    btn_pdf.pack(side='right')

    # ── Cabeçalho da lista ──────────────────────────────────────────────────
    emp_hdr = ctk.CTkFrame(left, fg_color='transparent')
    emp_hdr.pack(fill='x', pady=(4, 6))
    ctk.CTkLabel(emp_hdr, text='FUNCIONÁRIOS', font=F_SECTION,
                 text_color=DIM1).pack(side='left')
    var_summary = tk.StringVar()
    ctk.CTkLabel(emp_hdr, textvariable=var_summary, font=F_LABEL,
                 text_color=DIM2).pack(side='left', padx=(10, 0))

    # ── Painel inferior (fixo) — declarado antes do scroll para ancorar no fundo ──
    bottom = ctk.CTkFrame(left, fg_color='transparent')
    bottom.pack(side='bottom', fill='x', pady=(4, 0))

    # ── Lista scrollável ─────────────────────────────────────────────────────
    scroll = ctk.CTkScrollableFrame(left, fg_color=SURFACE,
                                    corner_radius=8, border_width=1, border_color=BORDER)
    scroll.pack(fill='both', expand=True, pady=(0, 8))

    # Frame interno recriável — evita corrupção de estado do CTkScrollableFrame
    list_frame = [ctk.CTkFrame(scroll, fg_color='transparent')]
    list_frame[0].pack(fill='x')

    def _make_list_frame():
        try:
            list_frame[0].destroy()
        except Exception:
            pass
        list_frame[0] = ctk.CTkFrame(scroll, fg_color='transparent')
        list_frame[0].pack(fill='x')

    # ── Bottom bar ───────────────────────────────────────────────────────────
    actions = ctk.CTkFrame(bottom, fg_color='transparent')
    actions.pack(fill='x', pady=(0, 10))

    btn_sel = ctk.CTkButton(actions, text='Selecionar todos', width=120, height=24,
                             fg_color='transparent', hover_color=SURFACE2,
                             text_color=DIM2, border_width=0,
                             font=F_LABEL, corner_radius=4, state='disabled')
    btn_sel.pack(side='left', padx=(0, 4))

    btn_desel = ctk.CTkButton(actions, text='Desmarcar todos', width=120, height=24,
                               fg_color='transparent', hover_color=SURFACE2,
                               text_color=DIM2, border_width=0,
                               font=F_LABEL, corner_radius=4, state='disabled')
    btn_desel.pack(side='left')

    var_status = tk.StringVar()
    lbl_status = ctk.CTkLabel(bottom, textvariable=var_status, font=F_LABEL,
                               text_color=DIM2, anchor='w')
    lbl_status.pack(fill='x', pady=(0, 6))

    progress = ctk.CTkProgressBar(bottom, mode='indeterminate',
                                   progress_color=ACCENT, fg_color=SURFACE2,
                                   height=3, corner_radius=2)
    progress.pack(fill='x', pady=(0, 14))
    progress.set(0)

    btn_gerar = ctk.CTkButton(bottom, text='Gerar Recibos', height=44,
                               fg_color=ACCENT, hover_color=ACCENT_H,
                               text_color='#ffffff', font=F_BUTTON, corner_radius=8)
    btn_gerar.pack(fill='x')

    # ── Painel de preview (right) ────────────────────────────────────────────
    prev_hdr = ctk.CTkFrame(right, fg_color='transparent')
    prev_hdr.pack(fill='x', pady=(0, 8))

    ctk.CTkLabel(prev_hdr, text='PRÉVIA', font=F_SECTION,
                 text_color=DIM1).pack(side='left')

    nav_frame = ctk.CTkFrame(prev_hdr, fg_color='transparent')
    nav_frame.pack(side='right')

    _NAV_BTN = dict(width=36, height=32, fg_color=SURFACE2, hover_color='#3a3a3a',
                    text_color=TEXT, border_color=BORDER, border_width=1,
                    font=ctk.CTkFont('Segoe UI', 14), corner_radius=6)

    btn_prev_p = ctk.CTkButton(nav_frame, text='←', state='disabled', **_NAV_BTN)
    btn_prev_p.pack(side='left', padx=(0, 4))

    lbl_nav = ctk.CTkLabel(nav_frame, text='', font=F_LABEL, text_color=DIM2, width=60)
    lbl_nav.pack(side='left')

    btn_next_p = ctk.CTkButton(nav_frame, text='→', state='disabled', **_NAV_BTN)
    btn_next_p.pack(side='left', padx=(4, 0))

    prev_scroll = ctk.CTkScrollableFrame(right, fg_color=SURFACE,
                                         corner_radius=8, border_width=1,
                                         border_color=BORDER)
    prev_scroll.pack(fill='both', expand=True)

    prev_label = ctk.CTkLabel(prev_scroll, text='Selecione uma planilha\npara ver a prévia.',
                               font=F_LABEL, text_color=DIM2, anchor='center')
    prev_label.pack(anchor='center', pady=16)
    prev_label._ctk_img_ref = None

    _prev_idx      = [0]
    _preview_job   = [None]
    _preview_token = [None]

    def _clear_preview_image():
        """CTkLabel._update_image() não limpa o widget tkinter quando image=None,
        deixando uma referência pendente ao PhotoImage. Se o CTkImage for coletado
        pelo GC primeiro, qualquer configure() subsequente lança TclError.
        Solução: limpar o widget tkinter diretamente antes de liberar o CTkImage."""
        prev_label._ctk_img_ref = None
        try:
            prev_label._label.configure(image='')
        except Exception:
            pass

    def _get_selecionados():
        return [f for (v, *_), f in zip(checks_vars, funcionarios_carregados) if v.get()]

    def _atualizar_preview(*_):
        _preview_job[0] = None  # job consumido — evita cancel de ID já executado
        selecionados = _get_selecionados()

        if not selecionados:
            _clear_preview_image()
            prev_label.configure(image=None, text='Nenhum funcionário selecionado.')
            lbl_nav.configure(text='')
            btn_prev_p.configure(state='disabled')
            btn_next_p.configure(state='disabled')
            return

        n   = len(selecionados)
        idx = max(0, min(_prev_idx[0], n - 1))
        _prev_idx[0] = idx

        lbl_nav.configure(text=f'{idx + 1} / {n}')
        btn_prev_p.configure(state='normal' if idx > 0     else 'disabled')
        btn_next_p.configure(state='normal' if idx < n - 1 else 'disabled')

        prev_scroll.update_idletasks()
        pw   = min(480, max(260, prev_scroll.winfo_width() - 28))
        func = selecionados[idx]

        token = object()
        _preview_token[0] = token

        def _render():
            try:
                pil_img = gerar_preview_pil(func, width=pw)
            except Exception as exc:
                log.warning('Erro ao renderizar prévia: %s', exc)
                return
            if _preview_token[0] is not token:
                return  # requisição mais recente já em andamento — descarta
            def _apply():
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                        size=(pil_img.width, pil_img.height))
                _clear_preview_image()
                prev_label.configure(image=ctk_img, text='')
                prev_label._ctk_img_ref = ctk_img
            root.after(0, _apply)

        threading.Thread(target=_render, daemon=True).start()

    def _prev_receipt():
        _prev_idx[0] = max(0, _prev_idx[0] - 1)
        _atualizar_preview()

    def _next_receipt():
        _prev_idx[0] = min(len(_get_selecionados()) - 1, _prev_idx[0] + 1)
        _atualizar_preview()

    btn_prev_p.configure(command=_prev_receipt)
    btn_next_p.configure(command=_next_receipt)

    def _on_resize(event):
        if _preview_job[0]:
            root.after_cancel(_preview_job[0])
        _preview_job[0] = root.after(180, _atualizar_preview)

    right.bind('<Configure>', _on_resize)

    # ── Estado ─────────────────────────────────────────────────────────────
    checks_vars = []
    funcionarios_carregados = []

    def set_status(msg, color=DIM2):
        var_status.set(msg)
        lbl_status.configure(text_color=color)

    def selecionar_todos():
        for var, *_ in checks_vars:
            var.set(True)

    def desmarcar_todos():
        for var, *_ in checks_vars:
            var.set(False)

    btn_sel.configure(command=selecionar_todos)
    btn_desel.configure(command=desmarcar_todos)

    def _set_actions(enabled: bool):
        state = 'normal' if enabled else 'disabled'
        color = TEXT if enabled else DIM2
        btn_sel.configure(state=state, text_color=color)
        btn_desel.configure(state=state, text_color=color)

    def _atualizar_summary(*_):
        selecionados = [f for (v, *__), f in zip(checks_vars, funcionarios_carregados) if v.get()]
        n     = len(selecionados)
        total = sum(f['total'] for f in selecionados)
        var_summary.set(f'— {n} funcionário(s)  ·  {fmt_valor(total)}')
        if _preview_job[0]:
            root.after_cancel(_preview_job[0])
        _preview_job[0] = root.after(180, _atualizar_preview)

    def _clear_scroll():
        if _preview_job[0]:
            root.after_cancel(_preview_job[0])
            _preview_job[0] = None
        _preview_token[0] = None

        # Remove only OUR traces before destroying widgets — keeps CTkCheckBox's
        # internal trace intact so its .destroy() can clean up without TclError.
        for var, _nome, trace_id in checks_vars:
            try:
                var.trace_remove('write', trace_id)
            except Exception:
                pass
        checks_vars.clear()
        funcionarios_carregados.clear()

        _make_list_frame()

        var_summary.set('')
        _set_actions(False)
        _prev_idx[0] = 0
        lbl_nav.configure(text='')
        btn_prev_p.configure(state='disabled')
        btn_next_p.configure(state='disabled')
        _clear_preview_image()
        prev_label.configure(image=None, text='Selecione uma planilha\npara ver a prévia.')

    def _empty_state(text, color=DIM2):
        ctk.CTkLabel(list_frame[0], text=text, font=F_LABEL, text_color=color).pack(
            pady=32, padx=16)

    def carregar_funcionarios(caminho_xlsx: str, sheet_name=0):
        log.info('carregar_funcionarios: arquivo=%r aba=%r', caminho_xlsx, sheet_name)
        try:
            _clear_scroll()
        except Exception as exc:
            log.error('_clear_scroll falhou: %s', exc, exc_info=True)

        if not caminho_xlsx or not os.path.exists(caminho_xlsx):
            log.warning('carregar_funcionarios: arquivo nao encontrado: %r', caminho_xlsx)
            _empty_state('Selecione uma planilha para começar.')
            return

        try:
            funcionarios = ler_funcionarios(caminho_xlsx, sheet_name=sheet_name)
        except Exception as exc:
            log.warning('carregar_funcionarios: erro ao ler planilha: %s', exc)
            _empty_state(f'Erro ao ler planilha: {exc}', ERR)
            return

        log.info('carregar_funcionarios: %d funcionario(s) carregados', len(funcionarios))

        if not funcionarios:
            _empty_state('Nenhum funcionário encontrado nesta aba.')
            return

        funcionarios_carregados.extend(funcionarios)

        for func in funcionarios:
            var = tk.BooleanVar(value=True)
            trace_id = var.trace_add('write', _atualizar_summary)
            checks_vars.append((var, func['nome'], trace_id))

            row = ctk.CTkFrame(list_frame[0], fg_color='transparent')
            row.pack(fill='x', padx=8, pady=2)

            cb = ctk.CTkCheckBox(row, text='', variable=var, width=20,
                                  fg_color=ACCENT, hover_color=ACCENT_H,
                                  checkmark_color='#ffffff', corner_radius=4)
            cb.pack(side='left', padx=(4, 0))

            lbl_nome = ctk.CTkLabel(row, text=func['nome'],
                                     font=ctk.CTkFont('Segoe UI', 12),
                                     text_color=TEXT, anchor='w')
            lbl_nome.pack(side='left', fill='x', expand=True, padx=(8, 0))

            lbl_val = ctk.CTkLabel(row, text=fmt_valor(func['total']),
                                    font=ctk.CTkFont('Segoe UI', 11),
                                    text_color=DIM2, anchor='e')
            lbl_val.pack(side='right', padx=(0, 8))


        _atualizar_summary()
        _set_actions(True)

    # ── Callbacks ───────────────────────────────────────────────────────────
    def _on_aba(value):
        if value:
            carregar_funcionarios(var_xlsx.get().strip(), sheet_name=value)

    combo_aba.configure(command=_on_aba)

    def selecionar_xlsx():
        caminho = filedialog.askopenfilename(
            title='Selecionar planilha',
            filetypes=[('Excel', '*.xlsx *.xls'), ('Todos', '*.*')],
        )
        if not caminho:
            return
        var_xlsx.set(caminho)
        if not var_pdf.get():
            var_pdf.set(os.path.splitext(caminho)[0] + '_recibos.pdf')
        try:
            abas = pd.ExcelFile(caminho).sheet_names
        except Exception as exc:
            combo_aba.configure(values=[], state='disabled')
            var_aba.set('')
            set_status(f'Erro ao ler abas: {exc}', ERR)
            return
        if abas:
            combo_aba.configure(values=abas, state='normal')
            var_aba.set(abas[0])
            carregar_funcionarios(caminho, sheet_name=abas[0])
        else:
            combo_aba.configure(values=[], state='disabled')
            var_aba.set('')
            carregar_funcionarios(caminho)

    def selecionar_pdf():
        caminho = filedialog.asksaveasfilename(
            title='Salvar PDF como', defaultextension='.pdf',
            filetypes=[('PDF', '*.pdf')],
        )
        if caminho:
            var_pdf.set(caminho)

    btn_xlsx.configure(command=selecionar_xlsx)
    btn_pdf.configure(command=selecionar_pdf)

    def executar():
        xlsx = var_xlsx.get().strip()
        pdf  = var_pdf.get().strip()
        set_status('')

        if not xlsx:
            set_status('Selecione uma planilha (.xlsx).', ERR)
            return
        if not os.path.exists(xlsx):
            set_status(f'Arquivo não encontrado: {xlsx}', ERR)
            return
        if not pdf:
            pdf = os.path.splitext(xlsx)[0] + '_recibos.pdf'
            var_pdf.set(pdf)

        if checks_vars:
            funcionarios_sel = [
                f for (var, *_), f in zip(checks_vars, funcionarios_carregados)
                if var.get()
            ]
            if not funcionarios_sel:
                set_status('Selecione ao menos um funcionário.', ERR)
                return
        else:
            funcionarios_sel = list(funcionarios_carregados)

        btn_gerar.configure(state='disabled')
        progress.start()
        set_status('Gerando PDF...')

        def tarefa():
            try:
                gerar_pdf_de_lista(funcionarios_sel, pdf)
                root.after(0, lambda: concluido(pdf))
            except Exception as exc:
                msg = str(exc)
                root.after(0, lambda: erro(msg))

        threading.Thread(target=tarefa, daemon=True).start()

    def concluido(pdf_path):
        progress.stop()
        progress.set(0)
        btn_gerar.configure(state='normal')
        set_status('PDF gerado com sucesso.', ACCENT)
        if messagebox.askyesno('Concluído', f'PDF gerado:\n{pdf_path}\n\nDeseja abrir o arquivo?'):
            try:
                os.startfile(pdf_path)
            except OSError as exc:
                log.warning('Não foi possível abrir o PDF: %s', exc)

    def erro(msg):
        progress.stop()
        progress.set(0)
        btn_gerar.configure(state='normal')
        set_status(f'Erro: {msg}', ERR)

    btn_gerar.configure(command=executar)
    root.mainloop()


def main():
    if len(sys.argv) < 2:
        iniciar_gui()
        return

    arquivo_xlsx = sys.argv[1]
    if not os.path.exists(arquivo_xlsx):
        log.error('Arquivo não encontrado: %s', arquivo_xlsx)
        sys.exit(1)

    arquivo_pdf = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(arquivo_xlsx)[0] + '_recibos.pdf'
    gerar_pdf(arquivo_xlsx, arquivo_pdf)


if __name__ == '__main__':
    setup_logging()
    main()
