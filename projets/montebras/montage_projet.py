"""Montebras — découpage. Vidéo muette, sous-titres karaoké au rythme de lecture.

Les séquences chiffrées (frise, tonnage, métaux rares, fiches des minéraux, final) sont
composées avec HyperFrames : python3 projets/montebras/hyperframes_scenes.py

python3 projets/montebras/montage_projet.py            -> vidéo
python3 projets/montebras/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
import montage  # noqa: E402
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

# photos claires (turquoise, wavellite) : voile plus dense sous les sous-titres karaoké
montage.VOILE_FORCE = 0.68
montage.VOILE_SOUS_TITRES = montage._voile_sous_titres()

ARCH = "archives/retenues/"


def hf(nom, debut_sur):
    return Plan(f"hf/{nom}.mp4", debut_sur, "video")


PLANS = [
    # l'exploitation
    Plan(ARCH + "V1.jpg", "Montebras, dans la Creuse", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.47, 1.12)),
    Plan(ARCH + "A10.jpg", "Ses mines ont", "carte", depart=(0.45, 0.5, 1.0), arrivee=(0.55, 0.45, 1.15)),
    hf("frise_debut", "Selon les sources"),
    Plan(ARCH + "A8.jpg", "De 1868", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.6, 0.45, 1.15)),
    Plan(ARCH + "A3.jpg", "galeries", "carte", depart=(0.5, 0.55, 1.15), arrivee=(0.5, 0.5, 1.0)),
    Plan(ARCH + "A7.jpg", "laverie", "carte", depart=(0.4, 0.5, 1.0), arrivee=(0.55, 0.5, 1.12)),
    hf("etain_300t", "Au total"),
    hf("frise_fin", "Depuis 1965"),
    hf("metaux_rares", "Son granite"),
    Plan("photo_04_apatite.jpg", "de très beaux minéraux", depart=(0.55, 0.5, 1.5), arrivee=(0.5, 0.5, 1.0)),
    # quartz
    hf("fiche_quartz", "Le quartz est fait"),
    Plan("photo_01_quartz.jpg", "À Montebras, un épais", depart=(0.3, 0.52, 1.0), arrivee=(0.7, 0.5, 1.0),
         titres=[("Quartz", 0.05, 0.95)]),
    Plan("photo_02_quartz.jpg", "porte même un nom", depart=(0.5, 0.5, 1.0), arrivee=(0.45, 0.4, 1.35),
         titres=[("Quartz", 0.05, 0.95)]),
    Plan("photo_03_quartz.jpg", "Le quartz y forme", depart=(0.5, 0.35, 1.4), arrivee=(0.5, 0.5, 1.0),
         titres=[("Quartz", 0.05, 0.95)]),
    # apatite
    hf("fiche_apatite", "L'apatite est"),
    Plan("photo_05_apatite.jpg", "Mauve à violette", depart=(0.4, 0.45, 1.0), arrivee=(0.3, 0.33, 1.6),
         titres=[("Apatite", 0.05, 0.95)]),
    Plan("photo_06_apatite.jpg", "en cristaux atteignant", depart=(0.5, 0.5, 1.0), arrivee=(0.55, 0.42, 1.6),
         titres=[("Apatite", 0.05, 0.95)]),
    # fluorite
    hf("fiche_fluorite", "La fluorite est"),
    Plan("photo_07_fluorite.jpg", "et a donné son nom", depart=(0.5, 0.5, 1.0), arrivee=(0.42, 0.3, 1.5),
         titres=[("Fluorite", 0.05, 0.95)]),
    Plan("photo_08_fluorite.jpg", "À Montebras, elle forme", depart=(0.45, 0.4, 1.0), arrivee=(0.4, 0.35, 1.4),
         titres=[("Fluorite", 0.05, 0.95)]),
    # turquoise
    hf("fiche_turquoise", "La turquoise est"),
    Plan("photo_09_turquoise.jpg", "Sa couleur bleue", depart=(0.5, 0.55, 1.0), arrivee=(0.5, 0.62, 1.35),
         titres=[("Turquoise", 0.05, 0.95)]),
    Plan("photo_10_turquoise.jpg", "À Montebras, elle naît", depart=(0.5, 0.5, 1.0), arrivee=(0.62, 0.3, 1.6),
         titres=[("Turquoise", 0.05, 0.95)]),
    Plan("photo_09_turquoise.jpg", "Elle y colore", depart=(0.4, 0.6, 1.5), arrivee=(0.55, 0.55, 1.1),
         titres=[("Turquoise", 0.05, 0.95)]),
    # wavellite
    hf("fiche_wavellite", "La wavellite est"),
    Plan("photo_11_wavellite_sur_turquoise.jpg", "en gerbes rayonnantes", depart=(0.5, 0.5, 1.0),
         arrivee=(0.45, 0.45, 1.45), titres=[("Wavellite", 0.05, 0.95)]),
    Plan("photo_12_wavellite_sur_turquoise.jpg", "Décrite en 1805", depart=(0.45, 0.55, 1.0),
         arrivee=(0.35, 0.65, 1.4), titres=[("Wavellite", 0.05, 0.95)]),
    Plan("photo_11_wavellite_sur_turquoise.jpg", "Ici, ses gerbes", depart=(0.45, 0.42, 1.8),
         arrivee=(0.48, 0.45, 1.3), titres=[("Wavellite", 0.05, 0.95)]),
    # fin
    hf("final", "Toutes ces pièces"),
]

MOTS_CLES = ["Montebras", "étain", "l'étain", "feldspath", "quartz", "quartzglocke", "apatite", "fluorapatite",
             "fluorite", "turquoise", "wavellite"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots)
    return Projet(
        nom="montebras_v1_9x16",
        dossier=ICI,
        texte_voix=ICI / "texte_ecran.txt",
        audio_voix=None,
        mots=mots,
        plans=PLANS,
        generique=[],  # sources dans la description ; fin sur le logo seul
        logo="LOGO_jeremineralogie.jpg",
        mots_cles=MOTS_CLES,
        duree_generique=3.5,
        karaoke=True,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(rendre(projet(), apercu=[float(t) for t in sys.argv[1].split(",")]))
    else:
        print(rendre(projet()))
