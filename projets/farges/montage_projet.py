"""La pyromorphite des Farges — découpage. Vidéo muette : texte à l'écran seul.

python3 projets/farges/montage_projet.py            -> vidéo
python3 projets/farges/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

# Schéma 8 (formation) : centres des 5 étapes de la rangée du haut
ETAPES = [0.12, 0.31, 0.5, 0.69, 0.88]

PLANS = [
    Plan("photo_05.jpg", "Ce cristal vert", depart=(0.5, 0.45, 1.0), arrivee=(0.35, 0.35, 1.6)),
    Plan("photo_09.jpg", "Il pourrait aider", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.55, 1.15),
         titres=[("Sols pollués", 0.05, 0.95)]),
    Plan("photo_10.jpg", "Mine des Farges", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.5, 1.0)),  # image entière (demande de l auteur)
    Plan("photo_03.jpg", "Une petite mine", depart=(0.5, 0.7, 1.05), arrivee=(0.5, 0.3, 1.05),
         titres=[("Fermée en 1981", 0.05, 0.95)]),
    Plan("photo_06.jpg", "On y extrayait", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.48, 1.7),
         titres=[("Galène", 0.05, 0.95)]),
    Plan("photo_04.webp", "Mais les mineurs", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.45, 1.1)),
    Plan("photo_12.jpg", "de cristaux verts", depart=(0.5, 0.55, 1.0), arrivee=(0.45, 0.6, 1.5),
         titres=[("Pyromorphite", 0.05, 0.95)]),
    Plan("photo_02.jpg", "Sans valeur", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.55, 0.45, 1.12),
         titres=[("Mine des Farges", 0.05, 0.95)]),
    Plan("photo_13.jpg", "un trésor pour", depart=(0.45, 0.4, 1.3), arrivee=(0.5, 0.45, 1.0),
         titres=[("Collections", 0.05, 0.95)]),
    # formation : on suit les 5 étapes du schéma, sans coupure
    Plan("photo_08.png", "Elle naît de la galène", "carte", format_carte=(980, 760),
         depart=(ETAPES[0], 0.36, 2.0), arrivee=(ETAPES[1], 0.36, 2.0), titres=[("Formation", 0.05, 0.95)]),
    Plan("photo_08.png", "L'eau de pluie", "carte", format_carte=(980, 760),
         depart=(ETAPES[1], 0.36, 2.0), arrivee=(ETAPES[2], 0.36, 2.0), coupe_franche=True,
         titres=[("Formation", 0.0, 0.95)]),
    Plan("photo_08.png", "Le plomb libéré", "carte", format_carte=(980, 760),
         depart=(ETAPES[2], 0.36, 2.0), arrivee=(ETAPES[3], 0.36, 2.0), coupe_franche=True,
         titres=[("Formation", 0.0, 0.95)]),
    Plan("photo_08.png", "Il recristallise", "carte", format_carte=(980, 760),
         depart=(ETAPES[3], 0.36, 2.0), arrivee=(ETAPES[4], 0.4, 1.8), coupe_franche=True,
         titres=[("Formation", 0.0, 0.95)]),
    Plan("photo_07.jpg", "c'est la pyromorphite", depart=(0.5, 0.55, 1.2), arrivee=(0.42, 0.6, 1.8),
         titres=[("Prismes à six faces", 0.05, 0.95)]),
    Plan("photo_11.jpg", "Le plomb y reste", depart=(0.55, 0.5, 1.0), arrivee=(0.55, 0.45, 1.4)),
    # dépollution : schéma sur la coupe de sol, en trois étapes
    Plan("schema_depollution_A.jpg", "En 1993", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.52, 1.08),
         titres=[("1993", 0.05, 0.95)]),
    Plan("schema_depollution_B.jpg", "un phosphate", "carte", depart=(0.5, 0.52, 1.08), arrivee=(0.5, 0.5, 1.15),
         titres=[("1993", 0.0, 0.95)]),
    Plan("schema_depollution_B.jpg", "Le plomb dissous", "carte", depart=(0.5, 0.5, 1.15), arrivee=(0.5, 0.52, 1.25),
         coupe_franche=True, titres=[("Plomb dissous : −96 %", 0.05, 0.95)]),
    Plan("schema_depollution_C.jpg", "Il précipite", "carte", depart=(0.5, 0.52, 1.25), arrivee=(0.5, 0.5, 1.0),
         titres=[("Pyromorphite", 0.05, 0.95)]),
    Plan("photo_09.jpg", "Testée depuis", "carte", depart=(0.5, 0.5, 1.1), arrivee=(0.5, 0.5, 1.0),
         titres=[("Sols pollués", 0.05, 0.95)]),
    Plan("photo_12.jpg", "prometteuse", depart=(0.5, 0.5, 1.3), arrivee=(0.55, 0.5, 1.05)),
    Plan("photo_01.jpg", "Un « déchet » de mine", depart=(0.5, 0.55, 1.0), arrivee=(0.45, 0.62, 1.4)),
    Plan("photo_05.jpg", "devenu trésor", depart=(0.35, 0.35, 1.6), arrivee=(0.5, 0.45, 1.0)),
]

MOTS_CLES = ["Farges", "pyromorphite", "galène", "phosphate", "plomb"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots)
    return Projet(
        nom="farges_v1_9x16",
        dossier=ICI,
        texte_voix=ICI / "texte_ecran.txt",
        audio_voix=None,
        mots=mots,
        plans=PLANS,
        generique=[],  # sources dans la description ; fin sur le logo seul
        logo="LOGO_jeremineralogie.jpg",
        mots_cles=MOTS_CLES,
        duree_generique=3.5,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(rendre(projet(), apercu=[float(t) for t in sys.argv[1].split(",")]))
    else:
        print(rendre(projet()))
