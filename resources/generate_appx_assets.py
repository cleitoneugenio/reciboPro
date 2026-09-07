"""
Gera os assets de ícone do ReciboPro — fiel ao design system (tile azul).

Identidade (ver "recibopro - Design System"): cor primária azul #2563EB→#1B4ECC,
verde #22C55E só como accent. O ícone é um tile azul gradiente com o documento
(header verde "recibopro" + seta verde de aprovação).

Estratégia de tamanho (regra do design system: wordmark omitido abaixo de 64px):
  - >= 64px : ilustração completa (icon_nobg_1024.png) composta sobre o tile azul.
  - <  64px : versão simplificada vetorial (tile azul + doc branco + header verde
              + seta verde), legível na barra de tarefas / Start.

Saídas:
  resources/appx/StoreLogo.png         (50x50,  full-bleed)
  resources/appx/Square44x44Logo.png   (44x44,  full-bleed — taskbar)
  resources/appx/Square150x150Logo.png (150x150,full-bleed — Start medium)
  resources/appx/Wide310x150Logo.png   (310x150,full-bleed — wide tile)
  resources/icon.png                   (512,    rounded — master)
  resources/icon.ico                   (16..256,rounded — .exe/NSIS/dev)
"""
from PIL import Image, ImageDraw

C1 = (37, 99, 235)    # #2563EB  (primary)
C2 = (27, 78, 204)    # #1B4ECC  (primary dark)
MID = (32, 88, 219)
GREEN = (34, 197, 94, 255)    # #22C55E accent
WHITE = (255, 255, 255, 255)
LINE = (143, 179, 240, 255)   # #8FB3F0
LINE2 = (192, 212, 245, 255)  # #C0D4F5
SS = 8

_ILLO = None


def illo():
    global _ILLO
    if _ILLO is None:
        im = Image.open("resources/icon_nobg_1024.png").convert("RGBA")
        _ILLO = im.crop(im.getbbox())
    return _ILLO


def gradient(S):
    g = Image.new("RGB", (2, 2))
    g.putpixel((0, 0), C1); g.putpixel((1, 1), C2)
    g.putpixel((1, 0), MID); g.putpixel((0, 1), MID)
    return g.resize((S, S), Image.BICUBIC).convert("RGBA")


def round_mask(S, r):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, S, S], radius=r, fill=255)
    return m


def base_tile(S, rounded):
    tile = gradient(S)
    if rounded:
        tile.putalpha(round_mask(S, int(S * 0.22)))
    return tile


def fit(img, box):
    """Escala mantendo proporção para caber em box×box (amplia ou reduz)."""
    scale = box / max(img.width, img.height)
    return img.resize((max(1, round(img.width * scale)),
                       max(1, round(img.height * scale))), Image.LANCZOS)


def large(size, rounded):
    S = size * SS
    tile = base_tile(S, rounded)
    img = fit(illo(), int(S * 0.84))
    tile.alpha_composite(img, ((S - img.width) // 2, (S - img.height) // 2))
    return tile.resize((size, size), Image.LANCZOS)


def small(size, rounded):
    S = size * SS
    tile = base_tile(S, rounded)
    d = ImageDraw.Draw(tile)
    dw, dh = int(S * 0.46), int(S * 0.56)
    x0, y0 = (S - dw) // 2 - int(S * 0.03), (S - dh) // 2
    x1, y1 = x0 + dw, y0 + dh
    rad = int(dw * 0.10)
    d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=WHITE)
    hh = int(dh * 0.24)
    d.rounded_rectangle([x0, y0, x1, y0 + hh], radius=rad, fill=GREEN)
    d.rectangle([x0, y0 + hh - rad, x1, y0 + hh], fill=GREEN)
    pad = int(dw * 0.16)
    lh = max(2, int(dh * 0.055))
    ly = y0 + hh + int(dh * 0.14)
    for wd, col in [(0.95, LINE), (0.7, LINE2), (0.82, LINE2)]:
        d.rounded_rectangle([x0 + pad, ly, x0 + pad + int((dw - 2 * pad) * wd), ly + lh],
                            radius=lh // 2 or 1, fill=col)
        ly += int(dh * 0.16)
    cr = int(dw * 0.22)
    cx, cy = x1, (y0 + y1) // 2 + int(dh * 0.05)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=GREEN)
    aw = cr * 0.5
    w = max(2, int(cr * 0.22))
    d.line([cx - aw, cy, cx + aw * 0.6, cy], fill=WHITE, width=w)
    d.line([cx + aw * 0.1, cy - aw * 0.6, cx + aw * 0.6, cy], fill=WHITE, width=w)
    d.line([cx + aw * 0.1, cy + aw * 0.6, cx + aw * 0.6, cy], fill=WHITE, width=w)
    return tile.resize((size, size), Image.LANCZOS)


def icon(size, rounded):
    return (large if size >= 64 else small)(size, rounded)


def main():
    out = "resources/appx"
    icon(50, False).save(f"{out}/StoreLogo.png")
    icon(44, False).save(f"{out}/Square44x44Logo.png")
    icon(150, False).save(f"{out}/Square150x150Logo.png")

    # wide tile: blue gradient + centered illustration
    wimg = base_tile(310 * SS, False)
    il = fit(illo(), int(150 * SS * 0.78))
    wimg.alpha_composite(il, ((310 * SS - il.width) // 2, (150 * SS - il.height) // 2))
    wimg.resize((310, 150), Image.LANCZOS).save(f"{out}/Wide310x150Logo.png")

    icon(512, True).save("resources/icon.png")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [icon(s, True) for s in sizes]
    imgs[-1].save("resources/icon.ico", format="ICO",
                  sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
    print("Ícones (azul) gerados.")


if __name__ == "__main__":
    main()
