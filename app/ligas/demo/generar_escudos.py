"""Genera los escudos PNG de los clubes ficticios y el logo de la liga demo.

Uso (desde la raíz del proyecto):  python -m app.ligas.demo.generar_escudos
Los PNG resultantes se versionan en app/static/escudos/demo/.
"""
import os

from PIL import Image, ImageDraw, ImageFont

from app.ligas.demo.clubes import CLUBES, monograma, slug

AQUI = os.path.dirname(__file__)
ESTATICOS = os.path.normpath(os.path.join(AQUI, "..", "..", "static"))
FUENTE = os.path.join(ESTATICOS, "fonts", "BarlowCondensed-Bold.ttf")
SALIDA = os.path.join(ESTATICOS, "escudos", "demo")
GRANDE, FINAL = 1024, 256  # se dibuja grande y se reduce para suavizar los bordes


def _rgb(hex_):
    hex_ = hex_.lstrip("#")
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4))


def _mezclar(color, con, cantidad):
    return tuple(int(c + (w - c) * cantidad) for c, w in zip(color, con))


def _escudo(color, texto):
    base = _rgb(color)
    img = Image.new("RGBA", (GRANDE, GRANDE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = GRANDE
    contorno = [(w * .5, w * .04), (w * .92, w * .17), (w * .92, w * .52), (w * .5, w * .96), (w * .08, w * .52), (w * .08, w * .17)]
    d.polygon(contorno, fill=(255, 255, 255, 255))
    margen = w * .045
    interior = [(w * .5, w * .04 + margen * 1.2), (w * .92 - margen, w * .17 + margen * .6), (w * .92 - margen, w * .52 - margen * .3),
                (w * .5, w * .96 - margen * 1.6), (w * .08 + margen, w * .52 - margen * .3), (w * .08 + margen, w * .17 + margen * .6)]
    d.polygon(interior, fill=base + (255,))
    # mitad derecha más oscura, como un escudo cuartelado
    oscuro = _mezclar(base, (0, 0, 0), .22)
    mitad = [(w * .5, w * .04 + margen * 1.2), (w * .92 - margen, w * .17 + margen * .6), (w * .92 - margen, w * .52 - margen * .3),
             (w * .5, w * .96 - margen * 1.6)]
    d.polygon(mitad, fill=oscuro + (255,))
    fuente = ImageFont.truetype(FUENTE, int(w * .42))
    d.text((w * .5, w * .46), texto, font=fuente, fill=(255, 255, 255, 255), anchor="mm")
    return img.resize((FINAL, FINAL), Image.LANCZOS)


def _logo():
    img = Image.new("RGBA", (GRANDE, GRANDE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((20, 20, GRANDE - 20, GRANDE - 20), fill=(255, 255, 255, 255))
    d.ellipse((90, 90, GRANDE - 90, GRANDE - 90), fill=_rgb("#0b1730") + (255,))
    d.arc((90, 90, GRANDE - 90, GRANDE - 90), 200, 340, fill=_rgb("#2dd4bf") + (255,), width=34)
    fuente = ImageFont.truetype(FUENTE, int(GRANDE * .30))
    d.text((GRANDE / 2, GRANDE / 2 + 6), "LRF", font=fuente, fill=(255, 255, 255, 255), anchor="mm")
    return img.resize((FINAL, FINAL), Image.LANCZOS)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, _localidad, color in CLUBES:
        _escudo(color, monograma(nombre)).save(os.path.join(SALIDA, f"{slug(nombre)}.png"), optimize=True)
    _logo().save(os.path.join(SALIDA, "logo.png"), optimize=True)
    print(f"Listo: {len(CLUBES)} escudos y el logo en {SALIDA}")


if __name__ == "__main__":
    main()
