"""
Ícone reciboPro — redesign bold.
Princípio: uma forma, dois blocos de cor, legível em 16px.

Estrutura:
  - Fundo: gradiente azul com cantos arredondados
  - Recibo: retângulo branco centralizado, grande
  - Topo do recibo: bloco verde sólido (40% da altura)
  - Corpo: 3 linhas bold azuis
  - Nenhum detalhe que desaparece em tamanho pequeno
"""

import os
import numpy as np
from PIL import Image, ImageDraw

BG_TOP  = (37,  99, 235)   # #2563EB
BG_BOT  = (27,  78, 204)   # #1B4ECC
WHITE   = (255, 255, 255)
GREEN   = (34,  197,  94)  # #22C55E
BLUE_LN = (99,  149, 220)  # linhas no corpo — contraste claro no branco


def gradient_bg(size):
    xs = np.arange(size, dtype=np.float32)
    ys = np.arange(size, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)
    t = (xx + yy) / (2 * (size - 1))
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    for c in range(3):
        arr[:, :, c] = (BG_TOP[c] + t * (BG_BOT[c] - BG_TOP[c])).astype(np.uint8)
    return Image.fromarray(arr, 'RGB')


def rounded_mask(size, radius):
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=255
    )
    return mask


def draw_icon(size: int) -> Image.Image:
    # ── Fundo ──────────────────────────────────────────────────────────────
    bg_radius = max(3, round(size * 0.22))   # ~22% → arredondamento iOS-style
    bg = gradient_bg(size).convert('RGBA')
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(bg, mask=rounded_mask(size, bg_radius))
    draw = ImageDraw.Draw(result)

    # ── Recibo ─────────────────────────────────────────────────────────────
    # Margens: 16% esquerda/direita, 14% cima/baixo
    margin_h = round(size * 0.16)
    margin_v = round(size * 0.14)
    rx1 = margin_h
    ry1 = margin_v
    rx2 = size - margin_h
    ry2 = size - margin_v

    paper_r = max(2, round(size * 0.06))
    draw.rounded_rectangle([rx1, ry1, rx2, ry2], radius=paper_r, fill=WHITE + (255,))

    # ── Header verde — 38% da altura do papel ──────────────────────────────
    paper_h = ry2 - ry1
    split = ry1 + round(paper_h * 0.38)

    # Parte superior (cantos arredondados só em cima)
    draw.rounded_rectangle([rx1, ry1, rx2, split], radius=paper_r, fill=GREEN + (255,))
    # Preenche a área de junção para não deixar gap
    draw.rectangle([rx1, split - paper_r, rx2, split], fill=GREEN + (255,))

    # ── Linhas de conteúdo no corpo branco ─────────────────────────────────
    # 3 linhas bold, espaçadas uniformemente no corpo
    body_top    = split + round(paper_h * 0.10)
    body_bottom = ry2   - round(paper_h * 0.12)
    body_h      = body_bottom - body_top
    line_pad_h  = round((rx2 - rx1) * 0.12)
    line_lx     = rx1 + line_pad_h
    line_rx     = rx2 - line_pad_h
    line_w      = max(1, round(size * 0.045))   # espessura da linha

    widths = [1.0, 0.70, 0.82]   # comprimentos relativos das 3 linhas
    for i, w in enumerate(widths):
        t = i / (len(widths) - 1)   # 0 … 1
        ly = round(body_top + t * body_h)
        lx2 = line_lx + round((line_rx - line_lx) * w)
        draw.rounded_rectangle(
            [line_lx, ly - line_w // 2, lx2, ly + line_w - line_w // 2],
            radius=line_w // 2,
            fill=BLUE_LN + (230,),
        )

    return result


def main():
    out_dir = r'c:\Users\cleit\OneDrive\Documentos\reciboPro\resources'
    os.makedirs(out_dir, exist_ok=True)

    # PNG mestre 256px
    draw_icon(256).save(os.path.join(out_dir, 'icon.png'))
    print('icon.png')

    # ICO com todos os tamanhos
    sizes  = [16, 32, 48, 64, 128, 256]
    frames = [draw_icon(s).convert('RGBA') for s in sizes]
    frames[0].save(
        os.path.join(out_dir, 'icon.ico'),
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print('icon.ico')

    # Previews para inspeção
    for s in sizes:
        draw_icon(s).save(os.path.join(out_dir, f'icon_preview_{s}.png'))
    print('previews prontos')


if __name__ == '__main__':
    main()
