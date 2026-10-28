"""Fonds de carte lisibles (relief, sans géologie) : France entière et vues zoomées sur chaque gisement.

Mer et pays voisins sombres, France en relief ombré (IGN, estompage), limites des départements.
Sources : IGN Géoplateforme (WMS-R : estompage ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW ; Plan IGN v2,
utilisé seulement pour séparer la mer des terres) et Admin Express (contours des départements). Licence Ouverte.

python3 projets/fluorites/carte_fond.py   -> sources/carte/france.png + sources/carte/zoom_<n>.png
"""
import io
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ICI = Path(__file__).resolve().parent
CARTE = ICI / "sources" / "carte"
R = 6378137
WMS = "https://data.geopf.fr/wms-r/wms"

MER = np.array([10, 12, 19])
VOISINS = np.array([30, 27, 37])
TERRE = np.array([112, 100, 130])


def merc(lon, lat):
    return math.radians(lon) * R, R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def wms(couche, bbox, w, h, nx=1, ny=1):
    """Image WMS en tuiles (limite du service), en RGBA."""
    x0, y0, x1, y1 = bbox
    img = Image.new("RGBA", (w, h))
    tw, th = w // nx, h // ny
    for i in range(nx):
        for j in range(ny):
            b = (x0 + (x1 - x0) * i / nx, y1 - (y1 - y0) * (j + 1) / ny, x0 + (x1 - x0) * (i + 1) / nx, y1 - (y1 - y0) * j / ny)
            url = (f"{WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:3857&FORMAT=image/png"
                   f"&LAYERS={couche}&BBOX={','.join(map(str, b))}&WIDTH={tw}&HEIGHT={th}")
            for _ in range(5):
                r = subprocess.run(["curl", "-sS", "-m", "300", url], capture_output=True)
                try:
                    img.paste(Image.open(io.BytesIO(r.stdout)).convert("RGBA"), (i * tw, j * th))
                    break
                except Exception:
                    print("reprise", couche, i, j, r.stdout[:120], file=sys.stderr)
    return img


def departements():
    d = json.loads((CARTE / "departements.geojson").read_text())
    for f in d["features"]:
        if len(f["properties"]["code_insee"]) > 2:  # outre-mer
            continue
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        yield f["properties"]["code_insee"], [[merc(*p) for p in poly[0]] for poly in polys]


def rendre(bbox, w, h, nx=1, ny=1, trait=1.0):
    """Fond sombre en relief pour la boîte bbox (EPSG:3857), à w x h pixels."""
    x0, y0, x1, y1 = bbox

    def px(p):
        return ((p[0] - x0) / (x1 - x0) * w, (y1 - p[1]) / (y1 - y0) * h)

    plan = np.asarray(wms("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", bbox, w, h, nx, ny).convert("RGB")).astype(float)
    ombre = np.asarray(wms("ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW", bbox, w, h, nx, ny))[..., 3].astype(float) / 255
    # la mer du Plan IGN est bleu clair : b > r et b nettement > 190
    mer = (plan[..., 2] > 200) & (plan[..., 2] - plan[..., 0] > 25)
    # ouverture morphologique : efface les écritures du plan posées sur la mer
    terres = Image.fromarray((~mer * 255).astype(np.uint8))
    n = 3 if w < 2000 else 7
    mer = np.asarray(terres.filter(ImageFilter.MinFilter(n)).filter(ImageFilter.MaxFilter(n))) < 128
    masque = Image.new("L", (w, h))
    traits = Image.new("RGBA", (w, h))
    dm, dt = ImageDraw.Draw(masque), ImageDraw.Draw(traits)
    contours = []
    for _, polys in departements():
        for ring in polys:
            pts = [px(p) for p in ring]
            dm.polygon(pts, fill=255)
            contours.append(pts)
    for pts in contours:
        dt.line(pts + pts[:1], fill=(255, 255, 255, 70), width=max(1, round(1.4 * trait)), joint="curve")
    france = np.asarray(masque.filter(ImageFilter.GaussianBlur(0.6))).astype(float)[..., None] / 255
    relief = np.clip(ombre * 4.0, 0, 1)[..., None]
    terre = TERRE * (1.1 - 0.95 * relief)
    fond = np.where(mer[..., None], MER, VOISINS)
    rgb = fond * (1 - france) + terre * france
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    img.alpha_composite(traits)
    # frontière de la France
    bord = Image.fromarray((np.asarray(masque) > 127).astype(np.uint8) * 255).filter(ImageFilter.FIND_EDGES)
    bord = bord.crop((4, 4, w - 4, h - 4)).filter(ImageFilter.MaxFilter(3 if trait < 2 else 5))
    bord = Image.new("L", (w, h)).paste(bord, (4, 4)) or ImageOps.expand(bord, 4)
    contour = Image.new("RGBA", (w, h), (199, 125, 255, 0))
    contour.putalpha(bord.point(lambda v: 200 if v else 0))
    img.alpha_composite(contour)
    return img.convert("RGB")


if __name__ == "__main__":
    cadre = json.loads((CARTE / "cadre.json").read_text())
    if "--zooms" not in sys.argv:
        rendre(cadre["bbox"], cadre["w"], cadre["h"], 1, 2, trait=2.0).save(CARTE / "france.png")
        print("france.png")
    if "--france" not in sys.argv:
        for z in json.loads((CARTE / "zooms.json").read_text()):
            rendre(z["bbox"], 1080, 1920, trait=1.6).save(CARTE / f"zoom_{z['n']}.png")
            print("zoom", z["n"])
