"""Gisements de la vidéo, cadrage de la carte de la Creuse et des zooms (commun aux fonds et aux séquences HyperFrames).

Les points sont placés au centre de la commune (IGN, géocodage), jamais sur l'emplacement du gisement.
"""
import json
import math
from pathlib import Path

ICI = Path(__file__).resolve().parent
CARTE = ICI / "sources" / "carte"
R = 6378137
ZOOM = 4.5             # échelle de la vue zoomée (environ 27 km de large)
CIBLE = (540, 640)     # où arrive le point une fois zoomé

# nom affiché, sous-titre, code INSEE de la commune, lat, lon (chef-lieu), photo de la vignette, séquence carte dédiée
GISEMENTS = [
    ("Crozant", "", "23070", 46.389151, 1.619867, "photo_01.jpg", True),
    ("Anzême", "", "23004", 46.252258, 1.84694, "photo_05.jpg", True),
    ("Montebras", "Soumans", "23174", 46.29794, 2.337174, "photo_13.jpg", True),
    ("Janaillat", "", "23099", 46.047738, 1.7727, "photo_17.jpg", True),
    ("Lavaveix-les-Mines", "", "23105", 46.073309, 2.088493, "photo_09.jpg", True),
    ("Ahun", "", "23001", 46.088732, 2.021879, "photo_10.jpg", False),  # vu dans le zoom de Lavaveix
    ("Saint-Silvain-Bellegarde", "", "23241", 45.971118, 2.30385, "photo_07.jpg", True),
    ("Flayat", "Étang de la Ramade", "23081", 45.776991, 2.38448, "photo_04.jpg", True),
    ("Hyverneresse", "Gioux", "23091", 45.810063, 2.118847, "photo_02.jpg", True),
    ("Vallière", "Gour de Vaux", "23257", 45.906386, 2.040454, "photo_06.jpg", True),
]

# repères pour la vue d'ensemble
VILLES = [("Guéret", 46.171, 1.8717), ("Aubusson", 45.9559, 2.1682)]

# la Creuse (lon 1.37-2.61, lat 45.66-46.46) occupe x 110-970, centrée vers y 770
LARGEUR_CREUSE = 860
CENTRE_Y = 770


def merc(lon, lat):
    return math.radians(lon) * R, R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def calculer_cadre():
    """Boîte EPSG:3857 de la vue d'ensemble 1080 x 1920."""
    x0, y0 = merc(1.3725935, 45.66354575)
    x1, y1 = merc(2.61128487, 46.45536592)
    m = (x1 - x0) / LARGEUR_CREUSE  # mètres par pixel
    gx = x0 - 110 * m
    gy_haut = (y0 + y1) / 2 + CENTRE_Y * m
    return [gx, gy_haut - 1920 * m, gx + 1080 * m, gy_haut]


def cadre():
    return json.loads((CARTE / "cadre.json").read_text())["bbox"]


def ecran(lat, lon):
    """Position sur la vue d'ensemble (1080 x 1920)."""
    x0, y0, x1, y1 = cadre()
    x, y = merc(lon, lat)
    return (x - x0) / (x1 - x0) * 1080, (y1 - y) / (y1 - y0) * 1920


def vue_zoom(i):
    """Transformation (tx, ty, s) qui amène le gisement i en CIBLE, à l'échelle ZOOM."""
    px, py = ecran(*GISEMENTS[i][3:5])
    return CIBLE[0] - px * ZOOM, CIBLE[1] - py * ZOOM, ZOOM


def boite_zoom(i):
    """Boîte EPSG:3857 couverte par l'écran une fois zoomé sur le gisement i, et sa place sur la vue d'ensemble."""
    tx, ty, s = vue_zoom(i)
    gx0, gy0 = -tx / s, -ty / s
    gw, gh = 1080 / s, 1920 / s
    x0, y0, x1, y1 = cadre()
    mx = lambda u: x0 + u / 1080 * (x1 - x0)
    my = lambda v: y1 - v / 1920 * (y1 - y0)
    return [mx(gx0), my(gy0 + gh), mx(gx0 + gw), my(gy0)], (gx0, gy0, gw, gh)


def ecrire_cadre():
    CARTE.mkdir(parents=True, exist_ok=True)
    (CARTE / "cadre.json").write_text(json.dumps({"bbox": calculer_cadre(), "w": 3240, "h": 5760}))
    (CARTE / "zooms.json").write_text(json.dumps([{"n": i + 1, "bbox": boite_zoom(i)[0]}
                                                  for i, g in enumerate(GISEMENTS) if g[6]]))


if __name__ == "__main__":
    ecrire_cadre()
    for g in GISEMENTS:
        print(g[0], [round(v) for v in ecran(*g[3:5])])
