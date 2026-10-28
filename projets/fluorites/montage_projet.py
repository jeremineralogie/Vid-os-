"""Fluorites de France — découpage. Vidéo muette, sous-titres karaoké (rythme Uranium).

Fil conducteur : une carte de France en relief. Pour chaque gisement, la carte dézoome, le point apparaît,
la carte zoome dessus (séquences HyperFrames carte_1 … carte_8), puis viennent les photos de la collection.
Séquences animées : python3 projets/fluorites/hyperframes_scenes.py

python3 projets/fluorites/montage_projet.py            -> vidéo
python3 projets/fluorites/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
import montage  # noqa: E402
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

montage.VOILE_FORCE = 0.68
montage.VOILE_SOUS_TITRES = montage._voile_sous_titres()


def hf(nom, debut_sur):
    return Plan(f"hf/{nom}.mp4", debut_sur, "video")


def photo(n, debut_sur, titre, depart=(0.5, 0.45, 1.0), arrivee=(0.5, 0.4, 1.3)):
    return Plan(f"photo_{n:02d}.jpg", debut_sur, depart=depart, arrivee=arrivee, titres=[(titre, 0.04, 0.96)] if titre else [])


PLANS = [
    photo(1, "Fluorites de France", "Fluorites de France", (0.5, 0.48, 1.0), (0.5, 0.45, 1.3)),
    hf("fiche_fluorite", "La fluorite est un fluorure"),
    hf("production", "Depuis 1861"),
    # 1. La Barre
    hf("carte_1", "Premier arrêt"),
    photo(5, "Ses cubes sont bleus", "Fluorite · La Barre"),
    photo(2, "parfois zonés", "Fluorite · La Barre", (0.5, 0.45, 1.0), (0.55, 0.42, 1.4)),
    photo(3, "Certains reposent", "Fluorite · La Barre"),
    # 2. Bisage
    hf("carte_2", "Tout près, Bisage"),
    photo(14, "Ici, des cubes violets", "Fluorite · Bisage"),
    photo(15, "puis un cube jaune", "Fluorite · Bisage"),
    # 3. Le Beix
    hf("carte_3", "Plus au sud"),
    photo(19, "Le BRGM y signale", "Fluorite · Le Beix", (0.5, 0.45, 1.0), (0.48, 0.42, 1.35)),
    photo(20, "bleus ou bleu-vert", "Fluorite · Le Beix"),
    # 4. Buxières-les-Mines
    hf("carte_4", "Dans l'Allier"),
    photo(16, "Violette ou jaune", "Fluorite · Buxières-les-Mines"),
    photo(17, "elle y forme", "Fluorite · Buxières-les-Mines"),
    photo(18, "Le BRGM y note", "Fluorite · Buxières-les-Mines"),
    # 5. Chavaniac-Lafayette
    hf("carte_5", "En Haute-Loire"),
    photo(10, "Ici, de gros cubes", "Fluorite · Chavaniac-Lafayette"),
    photo(11, "violets à gris", "Fluorite · Chavaniac-Lafayette"),
    # 6. Saint-Péray
    hf("carte_6", "En Ardèche"),
    photo(22, "Elles y côtoient", "Fluorite · Saint-Péray"),
    photo(21, "et la calcite", "Fluorite · Saint-Péray"),
    # 7. Valzergues
    hf("carte_7", "Dans l'Aveyron"),
    hf("calas_1971", "En 1971"),
    photo(6, "Ici, du jaune miel", "Fluorite · Valzergues"),
    photo(9, "sous une bordure", "Fluorite · Valzergues"),
    # 8. Maxonchamp
    hf("carte_8", "Enfin, à l'est"),
    photo(25, "Sa fluorite est verte", "Fluorite · Maxonchamp"),
    photo(24, "Ici, des cristaux violets", "Fluorite · Maxonchamp"),
    photo(23, "avec des lames", "Fluorite · Maxonchamp"),
    hf("carte_fin", "Huit gisements"),
]

MOTS_CLES = ["fluorite", "Mohs", "fondant", "Puy-de-Dôme", "La Barre", "fantômes", "Bisage", "Le Beix", "Buxières-les-Mines",
             "Chavaniac-Lafayette", "La Fayette", "Saint-Péray", "Valzergues", "Calas", "Maxonchamp", "Vosges"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots, par_mot=0.32, base=0.75)
    return Projet(
        nom="fluorites_v1_9x16",
        dossier=ICI,
        texte_voix=ICI / "texte_ecran.txt",
        audio_voix=None,
        mots=mots,
        plans=PLANS,
        generique=[],  # sources dans la description ; fin sur le logo seul
        logo="LOGO_jeremineralogie.jpg",
        mots_cles=MOTS_CLES,
        duree_generique=3.8,
        karaoke=True,
        texte_logo="jeremineralogie.fr",
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(rendre(projet(), apercu=[float(t) for t in sys.argv[1].split(",")]))
    else:
        print(rendre(projet()))
