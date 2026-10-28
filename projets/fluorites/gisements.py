"""Gisements de la vidéo, cadrage de la carte de France et des zooms (commun aux fonds et aux séquences HyperFrames).

Les points sont placés au centre de la commune (IGN), jamais sur l'emplacement du gisement.
"""
import json
import math
from pathlib import Path

ICI = Path(__file__).resolve().parent
CARTE = ICI / "sources" / "carte"
R = 6378137
ZOOM = 9.0             # échelle de la vue zoomée (environ 230 km de large)
CIBLE = (540, 610)     # où arrive le point une fois zoomé

# nom affiché, sous-titre, département (code), lat, lon de la commune, photo de la vignette
GISEMENTS = [
    ("La Barre", "Saint-Jacques-d'Ambur", "Puy-de-Dôme", "63", 45.89339, 2.757132, "photo_01.jpg"),
    ("Bisage", "Puy-Saint-Gulmier", "Puy-de-Dôme", "63", 45.79077, 2.627279, "photo_14.jpg"),
    ("Le Beix", "près de Bourg-Lastic", "Puy-de-Dôme", "63", 45.727391, 2.544974, "photo_19.jpg"),
    ("Buxières-les-Mines", "", "Allier", "03", 46.471131, 2.943948, "photo_16.jpg"),
    ("Chavaniac-Lafayette", "", "Haute-Loire", "43", 45.156955, 3.581338, "photo_10.jpg"),
    ("Saint-Péray", "", "Ardèche", "07", 44.937982, 4.829871, "photo_22.jpg"),
    ("Valzergues", "", "Aveyron", "12", 44.505636, 2.226509, "photo_08.jpg"),
    ("Maxonchamp", "Rupt-sur-Moselle", "Vosges", "88", 47.934305, 6.653837, "photo_23.jpg"),
]

# repères pour la vue de France
VILLES = [("Paris", 48.8566, 2.3522), ("Lyon", 45.764, 4.8357), ("Marseille", 43.2965, 5.3698),
          ("Bordeaux", 44.8378, -0.5792), ("Strasbourg", 48.5734, 7.7521)]


def merc(lon, lat):
    return math.radians(lon) * R, R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def cadre():
    return json.loads((CARTE / "cadre.json").read_text())["bbox"]


def ecran(lat, lon):
    """Position sur la vue de France (1080 x 1920)."""
    x0, y0, x1, y1 = cadre()
    x, y = merc(lon, lat)
    return (x - x0) / (x1 - x0) * 1080, (y1 - y) / (y1 - y0) * 1920


def vue_zoom(i):
    """Transformation (tx, ty, s) qui amène le gisement i en CIBLE, à l'échelle ZOOM."""
    px, py = ecran(*GISEMENTS[i][4:6])
    return CIBLE[0] - px * ZOOM, CIBLE[1] - py * ZOOM, ZOOM


def boite_zoom(i):
    """Boîte EPSG:3857 couverte par l'écran une fois zoomé sur le gisement i, et sa place sur la vue de France."""
    tx, ty, s = vue_zoom(i)
    gx0, gy0 = -tx / s, -ty / s
    gw, gh = 1080 / s, 1920 / s
    x0, y0, x1, y1 = cadre()
    mx = lambda u: x0 + u / 1080 * (x1 - x0)
    my = lambda v: y1 - v / 1920 * (y1 - y0)
    return [mx(gx0), my(gy0 + gh), mx(gx0 + gw), my(gy0)], (gx0, gy0, gw, gh)


def ecrire_zooms():
    (CARTE / "zooms.json").write_text(json.dumps([{"n": i + 1, "bbox": boite_zoom(i)[0]} for i in range(len(GISEMENTS))]))


if __name__ == "__main__":
    ecrire_zooms()
    for i, g in enumerate(GISEMENTS):
        print(g[0], [round(v) for v in ecran(*g[4:6])])
