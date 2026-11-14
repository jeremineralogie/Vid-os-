"""Miniature verticale 1080 x 1920 : cristal héros (image rendue) + titre.

python3 miniature.py [image]   (par défaut : sources/rendu/int_1546.png, macro sur le grand cube)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
POLICE = "/usr/share/fonts/opentype/montserrat/Montserrat-{}.otf"


def texte_centre(d, y, lignes, police, couleur, interligne=1.12):
    for ligne in lignes:
        l = d.textlength(ligne, font=police)
        d.text(((1080 - l) / 2, y), ligne, font=police, fill=couleur)
        y += int(police.size * interligne)
    return y


def principal():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ICI / "sources/rendu/int_1546.png"
    im = Image.open(source).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    # voile dégradé en haut pour la lisibilité du titre
    voile = Image.new("L", (1080, 1920), 0)
    dv = ImageDraw.Draw(voile)
    for y in range(760):
        dv.line([(0, y), (1080, y)], fill=int(235 * (1 - y / 760) ** 1.1))
    noir = Image.new("RGB", im.size, (8, 8, 12))
    im = Image.composite(noir, im, voile)
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    gros = ImageFont.truetype(POLICE.format("ExtraBold"), 92)
    moyen = ImageFont.truetype(POLICE.format("SemiBold"), 42)
    y = texte_centre(d, 270, ["CE QUE TU", "NE VOIS PAS"], gros, (230, 230, 240, 255))
    y = texte_centre(d, y + 14, ["DANS UN SIMPLE CAILLOU"], moyen, (230, 230, 240, 255))
    d.rectangle([500, y + 26, 580, y + 30], fill=(118, 80, 201, 255))
    ombre = calque.filter(ImageFilter.GaussianBlur(8))
    im = im.convert("RGBA")
    im.alpha_composite(Image.eval(ombre, lambda v: v // 2))
    im.alpha_composite(calque)
    sortie = ICI / "exports/MINIATURE_CE_QUE_TU_NE_VOIS_PAS.jpg"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(sortie, quality=93)
    print(sortie)


if __name__ == "__main__":
    principal()
