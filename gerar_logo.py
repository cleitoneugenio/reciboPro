#!/usr/bin/env python3
"""
Gera logo_forte_telha.png a partir do design Forte Telha.
Requer: Pillow  (pip install pillow)
"""

import urllib.request
import os
from PIL import Image, ImageDraw, ImageFont

DIR = os.path.dirname(os.path.abspath(__file__))

# ── Baixar fontes Playfair Display ──────────────────────────────────────────
FONTS = {
    'playfair_bold': (
        'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/'
        'PlayfairDisplay%5Bwght%5D.ttf',
        os.path.join(DIR, '_PlayfairDisplay.ttf'),
    ),
    'playfair_sc': (
        'https://github.com/google/fonts/raw/main/ofl/playfairdisplaysc/'
        'PlayfairDisplaySC-Bold.ttf',
        os.path.join(DIR, '_PlayfairDisplaySC-Bold.ttf'),
    ),
}

for key, (url, path) in FONTS.items():
    if not os.path.exists(path):
        print(f'Baixando fonte {key}...')
        urllib.request.urlretrieve(url, path)
        print(f'  OK: {path}')

# ── Configurações ────────────────────────────────────────────────────────────
RED = (192, 57, 27)    # #C0391B
BG  = (0, 0, 0, 0)    # transparente

W, H = 960, 220

img  = Image.new('RGBA', (W, H), BG)
draw = ImageDraw.Draw(img)

# ── "FORTE TELHA" ────────────────────────────────────────────────────────────
try:
    font_title = ImageFont.truetype(FONTS['playfair_bold'][1], size=96)
except Exception:
    font_title = ImageFont.load_default()

title  = 'FORTE TELHA'
bbox_t = draw.textbbox((0, 0), title, font=font_title)
tw     = bbox_t[2] - bbox_t[0]
tx     = (W - tw) // 2
ty     = 8

draw.text((tx, ty), title, font=font_title, fill=RED)

# Posiciona subtítulo usando métricas reais da fonte (ascent + descent = altura visual total)
ascent, descent = font_title.getmetrics()
title_bottom = ty + ascent + descent  # linha inferior real do texto título

# ── Linha separadora fina ────────────────────────────────────────────────────
sep_y   = title_bottom + 10
sep_x0  = (W - tw) // 2 + 20
sep_x1  = (W + tw) // 2 - 20
draw.line([(sep_x0, sep_y), (sep_x1, sep_y)], fill=(*RED, 160), width=1)

# ── "INDÚSTRIA DE CERÂMICA" ──────────────────────────────────────────────────
try:
    font_sub = ImageFont.truetype(FONTS['playfair_sc'][1], size=24)
except Exception:
    font_sub = ImageFont.load_default()

subtitle        = 'INDÚSTRIA DE CERÂMICA'
subtitle_spaced = ' '.join(subtitle)   # espaçamento suave — 1 espaço entre chars

bbox_s = draw.textbbox((0, 0), subtitle_spaced, font=font_sub)
sw     = bbox_s[2] - bbox_s[0]
sx     = (W - sw) // 2
sy     = sep_y + 10

draw.text((sx, sy), subtitle_spaced, font=font_sub, fill=(*RED, 220))

# ── Crop ao conteúdo real + padding ─────────────────────────────────────────
bbox_content = img.getbbox()
if bbox_content:
    pad    = 14
    left   = max(0, bbox_content[0] - pad)
    top_c  = max(0, bbox_content[1] - pad)
    right  = min(W, bbox_content[2] + pad)
    bottom = min(H, bbox_content[3] + pad)
    img    = img.crop((left, top_c, right, bottom))

out = os.path.join(DIR, 'logo_forte_telha.png')
img.save(out, 'PNG')
print(f'Logo gerada: {out}  ({img.width}x{img.height}px)')
