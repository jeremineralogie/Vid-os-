"""Schéma « dépollution » dessiné sur la photo de coupe de sol (photo_09) : 3 étapes.
A : plomb dissous dans le sol ; B : ajout de phosphate ; C : plomb piégé en pyromorphite."""
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ICI = Path(__file__).resolve().parent
SRC = ICI / "sources/photo_09.jpg"


def police(nom, taille):
    chemin = subprocess.run(["fc-match", "-f", "%{file}", nom], capture_output=True, text=True).stdout
    return ImageFont.truetype(chemin, taille)


GRAS, MOYEN = police("Montserrat:style=Bold", 46), police("Montserrat:style=SemiBold", 34)
VIOLET, VIOLET_CLAIR = (123, 44, 191), (199, 125, 255)
GRIS_PB, VERT = (150, 155, 165), (139, 205, 60)

base = Image.open(SRC).convert("RGB")
base = base.resize((base.width * 2, base.height * 2), Image.LANCZOS)
W, H = base.size
rng = random.Random(3)
# particules de plomb dans les couches brunes et graveleuses (≈ 38 à 72 % de la hauteur)
points = [(rng.uniform(0.05, 0.95) * W, rng.uniform(0.40, 0.72) * H) for _ in range(30)]


def etiquette(d, xy, texte, couleur):
    x, y = xy
    l = d.textlength(texte, font=GRAS)
    d.rounded_rectangle((x - 22, y - 14, x + l + 22, y + 66), radius=18, fill=(11, 7, 16, 215))
    d.rectangle((x - 22, y + 58, x + l + 22, y + 66), fill=couleur + (255,))
    d.text((x, y), texte, font=GRAS, fill=(255, 255, 255, 255))


def hexagone(d, c, r, couleur):
    pts = [(c[0] + r * math.cos(math.pi / 3 * k), c[1] + r * math.sin(math.pi / 3 * k)) for k in range(6)]
    d.polygon(pts, fill=couleur + (255,), outline=(20, 40, 10, 255))


def etape(nom):
    im = base.copy().convert("RGBA")
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    for (x, y) in points:
        if nom == "C":
            hexagone(d, (x, y), 28, VERT)
        else:
            d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=GRIS_PB + (255,), outline=(30, 30, 35, 255), width=3)
            d.text((x - 19, y - 15), "Pb", font=police("Montserrat:style=Bold", 26), fill=(20, 20, 25, 255))
    if nom in "BC":
        for k in range(7):
            x = W * (0.1 + 0.13 * k)
            d.line((x, H * 0.04, x, H * 0.30), fill=VIOLET_CLAIR + (255,), width=10)
            d.polygon([(x - 24, H * 0.28), (x + 24, H * 0.28), (x, H * 0.34)], fill=VIOLET_CLAIR + (255,))
        if nom == "B":
            for _ in range(26):
                x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.38, 0.72) * H
                d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=VIOLET_CLAIR + (255,), outline=VIOLET + (255,), width=3)
    if nom == "A":
        etiquette(d, (40, 40), "Plomb dans le sol", GRIS_PB)
    elif nom == "B":
        etiquette(d, (40, 40), "Ajout de phosphate", VIOLET_CLAIR)
    else:
        etiquette(d, (40, 40), "Plomb piégé : pyromorphite", VERT)
    d.text((W - 190, H - 70), "Schéma", font=MOYEN, fill=(255, 255, 255, 230))
    im = Image.alpha_composite(im, calque).convert("RGB")
    im.save(ICI / f"sources/schema_depollution_{nom}.jpg", quality=95)


for n in "ABC":
    etape(n)
