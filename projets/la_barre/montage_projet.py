"""La mine de La Barre — découpage (voir SCRIPT.md). Vidéo muette : texte à l'écran seul.

python3 projets/la_barre/montage_projet.py            -> vidéo
python3 projets/la_barre/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

COUPE = "photo_14_coupe_sans_echelle.jpg"  # échelle retirée (accord de l'auteur)

PLANS = [
    Plan("photo_01.jpg", "Un cube", depart=(0.45, 0.55, 1.0), arrivee=(0.5, 0.53, 1.6)),
    Plan("photo_02.jpg", "Bienvenue", depart=(0.45, 0.1, 1.8), arrivee=(0.5, 0.5, 1.0),
         titres=[("Mine de La Barre", 0.1, 0.95)]),
    Plan("photo_12.jpg", "Saint-Jacques-d'Ambur", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.52, 0.42, 1.6),
         titres=[("Puy-de-Dôme", 0.05, 0.95)]),
    Plan("photo_11.jpg", "Au cœur", depart=(0.5, 0.5, 1.0), arrivee=(0.38, 0.33, 1.6),
         titres=[("District de Pontgibaud", 0.05, 0.95)]),
    Plan("photo_13.jpg", "Ici, la fluorine", depart=(0.5, 0.5, 1.0), arrivee=(0.45, 0.5, 1.4)),
    Plan(COUPE, "Des fluides chauds", depart=(0.45, 0.85, 2.0), arrivee=(0.45, 0.42, 2.0),
         titres=[("Fluides hydrothermaux", 0.05, 0.95)]),
    Plan("photo_09.jpg", "Le résultat", depart=(0.5, 0.7, 1.15), arrivee=(0.5, 0.3, 1.15),
         titres=[("Filon hydrothermal", 0.05, 0.95)]),
    Plan(COUPE, "Il traverse", "carte", format_carte=(980, 760), depart=(0.5, 0.5, 1.0), arrivee=(0.24, 0.27, 1.9),
         titres=[("Migmatites", 0.05, 0.95)]),
    Plan("photo_04.jpg", "Par endroits", depart=(0.5, 0.5, 1.3), arrivee=(0.5, 0.5, 1.0),
         titres=[("Fluorine massive", 0.05, 0.95)]),
    Plan(COUPE, "Ailleurs, des cavités", "carte", format_carte=(980, 760), depart=(0.5, 0.5, 1.0), arrivee=(0.75, 0.42, 1.9),
         titres=[("Cavités à cristaux", 0.05, 0.95)]),
    Plan("photo_02.jpg", "Des cubes bleus", depart=(0.3, 0.48, 1.35), arrivee=(0.7, 0.48, 1.35)),
    Plan("photo_03.jpg", "Certains montrent", depart=(0.5, 0.5, 1.0), arrivee=(0.45, 0.4, 1.5),
         titres=[("Zonation", 0.05, 0.95)]),
    Plan("photo_15.png", "On les appelle", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.5, 1.05),
         titres=[("Les fantômes", 0.05, 0.95)]),
    Plan("photo_15.png", "Le cube intérieur", depart=(0.5, 0.47, 1.0), arrivee=(0.5, 0.46, 1.5)),
    Plan("photo_15.png", "mais une ancienne", depart=(0.5, 0.46, 1.5), arrivee=(0.56, 0.4, 1.0),
         coupe_franche=True),
    Plan("photo_01.jpg", "Ces changements", depart=(0.55, 0.45, 1.9), arrivee=(0.6, 0.42, 2.2)),
    Plan("photo_05.jpg", "La fluorine se développe", depart=(0.5, 0.5, 1.0), arrivee=(0.4, 0.45, 1.4),
         titres=[("Quartz et calcédoine", 0.05, 0.95)]),
    Plan("photo_06.jpg", "Et parfois", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.35, 1.35),
         titres=[("Barytine", 0.05, 0.95)]),
    Plan("photo_10.jpg", "Mais à l'origine", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.55, 1.4),
         titres=[("Une mine industrielle", 0.05, 0.95)]),
    Plan("photo_04.jpg", "La fluorine servait", depart=(0.5, 0.3, 1.4), arrivee=(0.5, 0.35, 1.6),
         titres=[("Fondant métallurgique", 0.05, 0.95)]),
    Plan("photo_07.jpg", "Principale période", depart=(0.45, 0.5, 1.0), arrivee=(0.35, 0.33, 1.45),
         titres=[("1925 – 1947", 0.04, 0.45), ("70 000 à 100 000 t", 0.52, 0.96)]),
    Plan("photo_08.png", "Environ", depart=(0.5, 0.5, 1.15), arrivee=(0.48, 0.5, 1.0),
         titres=[("≈ 400 m de travaux", 0.05, 0.95)]),
    Plan("photo_09.jpg", "La mine ferme", depart=(0.5, 0.5, 1.3), arrivee=(0.5, 0.5, 1.0),
         titres=[("Fermeture vers 1948", 0.05, 0.95)]),
    Plan("photo_11.jpg", "Des recherches", depart=(0.38, 0.33, 1.6), arrivee=(0.45, 0.45, 1.15),
         titres=[("Années 1960", 0.05, 0.95)]),
    Plan("photo_02.jpg", "Aujourd'hui", depart=(0.7, 0.48, 1.35), arrivee=(0.3, 0.48, 1.35),
         titres=[("Collections", 0.05, 0.95)]),
    Plan("photo_03.jpg", "Mais une couleur", depart=(0.45, 0.4, 1.4), arrivee=(0.5, 0.5, 1.0)),
    Plan("photo_02.jpg", "Étiquettes", depart=(0.5, 0.4, 1.0), arrivee=(0.45, 0.06, 2.0),
         titres=[("La provenance", 0.05, 0.95)]),
    Plan("photo_01.jpg", "Et vous", depart=(0.5, 0.55, 1.0), arrivee=(0.5, 0.53, 1.3)),
]

MOTS_CLES = ["Barre", "fluorine", "Pontgibaud", "fantômes", "migmatites", "calcédoine", "barytine", "provenance"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots)
    return Projet(
        nom="la_barre_v1_9x16",
        dossier=ICI,
        texte_voix=ICI / "texte_ecran.txt",
        audio_voix=None,
        mots=mots,
        plans=PLANS,
        generique=[],  # sources citées par l'auteur dans la description ; fin sur le logo seul
        logo="LOGO_jeremineralogie.jpg",
        mots_cles=MOTS_CLES,
        duree_generique=3.5,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(rendre(projet(), apercu=[float(t) for t in sys.argv[1].split(",")]))
    else:
        print(rendre(projet()))
