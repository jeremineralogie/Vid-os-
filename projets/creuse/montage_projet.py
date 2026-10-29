"""Minéraux de la Creuse — découpage. Vidéo sans voix ni musique (l'auteur enregistrera sa voix), sous-titres karaoké.

Fil conducteur : une carte de la Creuse en relief. Pour chaque gisement, la carte dézoome, le point apparaît sur la
commune, la carte zoome (séquences HyperFrames carte_1 … carte_10), puis viennent les photos de la collection.
Montebras et Lavaveix ont une séquence d'archives avec compteurs. Séquences : python3 projets/creuse/hyperframes_scenes.py

python3 projets/creuse/montage_projet.py            -> vidéo
python3 projets/creuse/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
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
    photo(13, "Minéraux de la Creuse", "Minéraux de la Creuse", (0.5, 0.5, 1.0), (0.5, 0.45, 1.25)),
    # 1. Crozant (cartes postales anciennes dans la séquence carte)
    hf("carte_1", "Premier arrêt"),
    photo(1, "Ici, une calcédoine", "Calcédoine · Crozant"),
    photo(1, "Elle se dépose", "Calcédoine · Crozant", (0.5, 0.42, 1.3), (0.55, 0.4, 1.6)),
    # 2. Anzême
    hf("carte_2", "Tout près, à Anzême"),
    photo(5, "Ce sont des cubes", "Fluorite · Anzême"),
    # 3. Montebras
    hf("carte_3", "À l'est, Montebras"),
    hf("montebras", "Son étain est exploité"),
    photo(12, "Ici, un grand cristal", "Quartz · Montebras"),
    photo(15, "Voici de l'apatite", "Apatite · Montebras"),
    photo(16, "C'est la même famille", "Apatite · Montebras"),
    photo(14, "La turquoise et la wavellite", "Turquoise · Montebras"),
    photo(11, "La wavellite pousse", "Wavellite · Montebras"),
    photo(13, "Et voici une fluorite", "Fluorite et dolomite · Montebras", (0.5, 0.45, 1.0), (0.5, 0.42, 1.35)),
    # 4. Janaillat
    hf("carte_4", "À l'ouest, Janaillat"),
    photo(17, "Une roche rare", "Granite orbiculaire · Janaillat", (0.5, 0.4, 1.0), (0.5, 0.35, 1.25)),
    # 5. Lavaveix-les-Mines, puis Ahun (même secteur)
    hf("carte_5", "Au centre, Lavaveix-les-Mines"),
    hf("lavaveix", "Concédé en 1817"),
    photo(9, "Dans ma collection, cette pyrite", "Pyrite · Lavaveix-les-Mines"),
    photo(10, "Tout près, une carrière", "Calcite et analcime · Ahun"),
    photo(10, "Elle porte de l'analcime", "Calcite et analcime · Ahun", (0.42, 0.4, 1.4), (0.42, 0.35, 1.8)),
    # 6. Saint-Silvain-Bellegarde
    hf("carte_7", "À l'est, Saint-Silvain-Bellegarde"),
    photo(7, "Ici, une gerbe", "Quartz · Saint-Silvain-Bellegarde"),
    photo(8, "Puis de la calcite", "Calcite · Saint-Silvain-Bellegarde"),
    # 7. Flayat
    hf("carte_8", "Au sud-est, Flayat"),
    photo(4, "Sa fluorite violette", "Fluorite · Flayat"),
    # 8. Hyverneresse
    hf("carte_9", "À Gioux, Hyverneresse"),
    photo(2, "Ici, du béryl", "Béryl · Hyverneresse"),
    photo(3, "Il cristallise", "Béryl · Hyverneresse"),
    photo(18, "Et voici l'autunite", "Autunite · Hyverneresse"),
    # 9. Vallière
    hf("carte_10", "Enfin, Vallière"),
    photo(6, "Ici, de l'améthyste", "Améthyste · Vallière"),
    hf("carte_fin", "Dix gisements"),
]

MOTS_CLES = ["Creuse", "Crozant", "calcédoine", "botryoïdales", "Anzême", "fluorite", "Mohs", "Montebras", "montebrasite",
             "quartz", "apatite", "turquoise", "wavellite", "dolomite", "Janaillat", "orbiculaire", "Lavaveix-les-Mines",
             "pyrite", "Ahun", "calcite", "analcime", "Saint-Silvain-Bellegarde", "Flayat", "Hyverneresse", "béryl",
             "autunite", "Vallière", "améthyste"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots, par_mot=0.32, base=0.75)
    return Projet(
        nom="creuse_v1_9x16",
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
