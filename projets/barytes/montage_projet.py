"""Barytes miel du Puy-de-Dôme — découpage. Vidéo muette, sous-titres karaoké (rythme Uranium).

Toujours une image en rapport avec le sujet en fond : jamais de fond de charte violet
(plans « carte » sur leur propre image floutée, séquences HyperFrames sur photo ou document).
Séquences animées : python3 projets/barytes/hyperframes_scenes.py

python3 projets/barytes/montage_projet.py            -> vidéo
python3 projets/barytes/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
import montage  # noqa: E402
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

montage.VOILE_FORCE = 0.68
montage.VOILE_SOUS_TITRES = montage._voile_sous_titres()

ARCH = "archives/"


def hf(nom, debut_sur):
    return Plan(f"hf/{nom}.mp4", debut_sur, "video")


def photo(n, debut_sur, titre, depart, arrivee, coupe=False):
    return Plan(f"photo_{n:02d}.jpg", debut_sur, depart=depart, arrivee=arrivee,
                titres=[(titre, 0.04, 0.96)] if titre else [], coupe_franche=coupe)


def archive(fichier, debut_sur, titre, depart, arrivee, mode="carte"):
    return Plan(ARCH + fichier, debut_sur, mode, depart=depart, arrivee=arrivee,
                titres=[(titre, 0.05, 0.95)] if titre else [], fond="flou" if mode == "carte" else None)


def page_gonnard(n, debut_sur, cy):
    """Page du livre de Gonnard en large carte, cadrée sur le paragraphe cité, sur fond de sa couverture."""
    return Plan(ARCH + f"gonnard1870_p-{n}.png", debut_sur, "carte", format_carte=(920, 760),
                depart=(0.5, cy, 1.0), arrivee=(0.5, cy, 1.3), titres=[("Gonnard, 1870", 0.05, 0.95)],
                fond=ARCH + "gonnard1870_couverture_recadree.png")


PLANS = [
    photo(1, "Dans le Puy-de-Dôme", "Barytes miel", (0.5, 0.45, 1.0), (0.48, 0.4, 1.3)),
    hf("carte_gisements", "Ses gisements"),
    hf("fiche_baryte", "La baryte est un sulfate"),
    archive("portrait_hauy_tardieu.jpg", "Elle est étudiée ici", "René Just Haüy", (0.5, 0.38, 1.0), (0.5, 0.36, 1.25)),
    hf("hauy_1823", "En 1823"),
    archive("hauy1823_pdf135-135.png", "Parmi eux, la variété", "Haüy, 1823 · planche 37",
            (0.5, 0.5, 1.0), (0.78, 0.84, 2.6)),
    hf("gonnard_1870", "En 1870"),
    page_gonnard(16, "Il juge la baryte", 0.75),
    hf("gonnard_18", "Il y décrit 18"),
    page_gonnard(17, "Dans les fentes des arkoses", 0.29),
    # Royat · puy Chateix
    archive("gorge_royat_1830_cleveland.jpg", "À Royat, le puy", "Royat, 1830", (0.5, 0.45, 1.0), (0.42, 0.45, 1.25)),
    page_gonnard(19, "Une variété très complexe", 0.34),
    archive("g50_chateix.png", "Selon le BRGM", "Carte géologique · Royat", (0.5, 0.5, 1.0), (0.45, 0.5, 1.35), "plein"),
    photo(3, "Gonnard y note", "Baryte · puy Chateix", (0.5, 0.45, 1.0), (0.5, 0.38, 1.35)),
    photo(4, "Ici, de grands cristaux", "Baryte · puy Chateix", (0.5, 0.42, 1.0), (0.45, 0.38, 1.35)),
    photo(5, "du miel au brun", "Baryte · puy Chateix", (0.5, 0.42, 1.0), (0.5, 0.38, 1.4)),
    # Saint-Saturnin · Côte d'Abot
    archive("g50_saturnin.png", "Saint-Saturnin figurait", "Carte géologique · Saint-Saturnin",
            (0.5, 0.5, 1.0), (0.5, 0.5, 1.3), "plein"),
    photo(8, "Ici, une pièce", "Baryte · Côte d'Abot, Saint-Saturnin", (0.5, 0.42, 1.0), (0.55, 0.42, 1.35)),
    # Olloix · le Liauzun
    photo(7, "À Olloix", "Baryte · Le Liauzun, Olloix", (0.5, 0.42, 1.0), (0.48, 0.38, 1.35)),
    photo(6, "Ses cristaux y sont souvent", "Baryte · Le Liauzun, Olloix", (0.5, 0.45, 1.0), (0.55, 0.3, 1.6)),
    # Champeix
    photo(9, "À Champeix", "Baryte · Champeix", (0.5, 0.45, 1.0), (0.5, 0.4, 1.35)),
    photo(10, "grises à miel", "Baryte · Champeix", (0.5, 0.42, 1.0), (0.48, 0.4, 1.35)),
    # Saint-Babel
    archive("g50_babel.png", "À Saint-Babel", "Carte géologique · Saint-Babel", (0.5, 0.5, 1.0), (0.48, 0.52, 1.35), "plein"),
    photo(1, "Ici, deux pièces", "Baryte · Saint-Babel", (0.55, 0.42, 1.3), (0.5, 0.45, 1.0)),
    photo(2, "d'un jaune miel", "Baryte · Saint-Babel", (0.5, 0.42, 1.0), (0.5, 0.38, 1.3)),
    # Châtel-Guyon
    archive("chatelguyon1881_carte_chemin_de_fer.png", "À Châtel-Guyon", "Châtel-Guyon, 1881",
            (0.5, 0.45, 1.0), (0.35, 0.47, 2.0)),
    archive("g50_chatel.png", "ont déposé de beaux", "Carte géologique · Châtel-Guyon", (0.5, 0.5, 1.0), (0.55, 0.45, 1.3), "plein"),
    photo(11, "Aujourd'hui, le baryum", "Baryte · Châtel-Guyon", (0.5, 0.42, 1.0), (0.48, 0.4, 1.35)),
    hf("final", "Collection jeremineralogie"),
]

MOTS_CLES = ["baryte", "Puy-de-Dôme", "Haüy", "Gonnard", "Royat", "Chateix", "Saint-Saturnin", "Olloix", "Liauzun",
             "Champeix", "Saint-Babel", "Châtel-Guyon", "sceptrés"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots, par_mot=0.32, base=0.75)
    return Projet(
        nom="barytes_v1_9x16",
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
