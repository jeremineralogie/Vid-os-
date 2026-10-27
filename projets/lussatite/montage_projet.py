"""Lussatite, l'opale d'Auvergne — découpage (voir SCRIPT.md).

Maquette : python3 projets/lussatite/montage_projet.py maquette
Voix de synthèse travaillée : python3 projets/lussatite/montage_projet.py synthese
Version finale (voix de l'auteur) : python3 projets/lussatite/montage_projet.py finale
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
from montage import Plan, Projet, rendre  # noqa: E402

PLANS = [
    # accroche : on part d'une perle, on découvre le bitume
    Plan("02_perles_grappes_macro.png", "Des perles d'opale", depart=(0.42, 0.40, 1.35), arrivee=(0.5, 0.5, 1.0)),
    Plan("01_ensemble_perles_placage.jpg", "Voici la lussatite", "carte",
         depart=(0.5, 0.6, 1.0), arrivee=(0.36, 0.64, 1.7), titres=[("La lussatite", 0.05, 0.95)]),
    Plan("W3_lussat_1910.jpg", "Elle tire son nom", "carte", hauteur_carte=600,
         depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.45, 1.08), titres=[("Lussat · Puy-de-Dôme", 0.05, 0.95)]),
    Plan("I3_opale_structure.png", "Oubliez les opales", "carte",
         depart=(0.3, 0.48, 1.8), arrivee=(0.32, 0.5, 2.05), titres=[("Opale de bijouterie", 0.05, 0.95)]),
    Plan("02_perles_grappes_macro.png", "la lussatite forme de petites perles",
         depart=(0.58, 0.55, 1.2), arrivee=(0.6, 0.58, 1.38), coupe_franche=True),
    Plan("I1_portrait_mallard.jpg", "En 1890", "carte", hauteur_carte=700,
         depart=(0.5, 0.45, 1.0), arrivee=(0.5, 0.38, 1.12), titres=[("Ernest Mallard · 1890", 0.05, 0.95)]),
    Plan("I4_lussatite_structure.png", "Au microscope", "carte",
         depart=(0.75, 0.3, 1.8), arrivee=(0.78, 0.24, 2.4), titres=[("Au microscope : des fibres", 0.05, 0.95)]),
    Plan("01_ensemble_perles_placage.jpg", "Et il mesure", "carte",
         depart=(0.5, 0.6, 1.15), arrivee=(0.5, 0.6, 1.35), titres=[("Densité : 2,04", 0.05, 0.95)]),
    Plan("I4_lussatite_structure.png", "Aujourd'hui, on la range", "carte",
         depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.5, 1.05), titres=[("Une opale-CT", 0.05, 0.95)]),
    Plan("I2_quartz_structure.png", "Le quartz est très ordonné", "carte",
         depart=(0.4, 0.5, 1.2), arrivee=(0.81, 0.72, 2.1), titres=[("Quartz : ordonné", 0.05, 0.95)]),
    Plan("I3_opale_structure.png", "l'opale presque désorganisée", "carte",
         depart=(0.4, 0.5, 1.2), arrivee=(0.79, 0.72, 2.1), titres=[("Opale : désordonnée", 0.05, 0.95)]),
    Plan("I4_lussatite_structure.png", "La lussatite, elle, est", "carte",
         depart=(0.4, 0.5, 1.2), arrivee=(0.82, 0.72, 2.25), titres=[("Opale-CT : feuillets empilés", 0.05, 0.95)]),
    # formation
    Plan("W2_puy_de_mur_dallet.jpg", "Comment s'est-elle formée", "carte",
         depart=(0.5, 0.5, 1.15), arrivee=(0.5, 0.5, 1.0), titres=[("La Limagne", 0.05, 0.95)]),
    Plan("I5_coupe_limagne.jpg", "Les boues calcaires", "carte", format_carte=(980, 520),
         depart=(0.0, 0.66, 1.25), arrivee=(0.0, 0.56, 1.25), titres=[("Calcaire et bitume", 0.05, 0.95)]),
    Plan("I5_coupe_limagne.jpg", "Puis les volcans", "carte", format_carte=(980, 520),
         depart=(0.0, 0.48, 1.25), arrivee=(0.0, 0.38, 1.25), titres=[("Coulée basaltique", 0.05, 0.95)]),
    Plan("W1_peperite_puy_de_crouel.jpg", "Le magma rencontre", "carte",
         depart=(0.5, 0.5, 1.0), arrivee=(0.42, 0.62, 1.35), titres=[("Pépérite · Puy de Crouel", 0.05, 0.95)]),
    Plan("I5_coupe_limagne.jpg", "De l'eau chaude", "carte", format_carte=(980, 520),
         depart=(0.42, 0.6, 1.25), arrivee=(0.76, 0.62, 1.25), titres=[("Eau chaude chargée de silice", 0.05, 0.95)]),
    Plan("02_perles_grappes_macro.png", "En refroidissant",
         depart=(0.4, 0.42, 1.0), arrivee=(0.4, 0.42, 1.18)),
    # formes
    Plan("01_ensemble_perles_placage.jpg", "Elle ne forme jamais", "carte",
         depart=(0.45, 0.6, 1.0), arrivee=(0.32, 0.68, 2.0), titres=[("Perles et grappes", 0.45, 0.95)]),
    Plan("04_fleur_sur_matrice.jpg", "en fleurs",
         depart=(0.45, 0.6, 1.0), arrivee=(0.42, 0.8, 1.7), titres=[("Fleur", 0.1, 0.9)]),
    Plan("01_ensemble_perles_placage.jpg", "ou en fines couches", "carte",
         depart=(0.6, 0.6, 1.4), arrivee=(0.7, 0.64, 2.2), titres=[("Placage", 0.1, 0.9)]),
    Plan("02_perles_grappes_macro.png", "Pure, elle est incolore",
         depart=(0.58, 0.52, 1.25), arrivee=(0.58, 0.52, 1.4)),
    # hélix et fossiles
    Plan("09_helix_cinq.jpg", "Les pièces les plus spectaculaires", "carte",
         depart=(0.5, 0.47, 1.0), arrivee=(0.5, 0.47, 1.08), titres=[("Helix ramondi", 0.3, 0.95)]),
    Plan("I4_lussatite_structure.png", "dont la coquille vide", "carte",
         depart=(0.3, 0.48, 1.8), arrivee=(0.3, 0.48, 2.0)),
    Plan("09_helix_cinq.jpg", "Parfois la coquille", "carte",
         depart=(0.13, 0.47, 2.4), arrivee=(0.78, 0.52, 2.4)),
    Plan("10_os_flamant_lussatite.jpg", "La lussatite a même",
         depart=(0.35, 0.5, 1.3), arrivee=(0.55, 0.35, 1.5), titres=[("Os de flamant", 0.15, 0.9)]),
    # gisements
    Plan("12_mine_des_rois_galerie.png", "Les plus beaux échantillons",
         depart=(0.5, 0.5, 1.0), arrivee=(0.55, 0.4, 1.15), titres=[("Mine des Rois · Dallet", 0.05, 0.95)]),
    Plan("W4_mine_des_rois_galerie.jpg", "Ses galeries sont", "carte", hauteur_carte=450,
         depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.5, 1.06)),
    Plan("W3_lussat_1910.jpg", "Le gisement d'origine", "carte", hauteur_carte=600,
         depart=(0.5, 0.45, 1.08), arrivee=(0.5, 0.5, 1.0), titres=[("Lussat · détruit en 1969", 0.05, 0.95)]),
    # pièges et conclusion
    Plan("15_rose_calcedoine_bresil.png", "Méfiez-vous", "carte",
         depart=(0.5, 0.5, 1.0), arrivee=(0.5, 0.5, 1.1), titres=[("Rose de calcédoine · Brésil", 0.05, 0.95)]),
    Plan("04_fleur_sur_matrice.jpg", "Une vraie lussatite",
         depart=(0.45, 0.62, 1.3), arrivee=(0.45, 0.55, 1.0), titres=[("Lussatite d'Auvergne", 0.05, 0.95)]),
    Plan("02_perles_grappes_macro.png", "Et vous",
         depart=(0.5, 0.5, 1.0), arrivee=(0.45, 0.42, 1.25)),
]

GENERIQUE = [
    "# Lussatite, l'opale d'Auvergne",
    "{credit_voix}",
    "# Photographies",
    "Spécimens, mine des Rois, illustrations et schémas : © jeremineralogie",
    "Ernest Mallard, portrait (XIXe siècle) — domaine public, via Wikimedia Commons",
    "Pépérite du Puy de Crouel — Romain Cadiou, CC BY-SA 3.0, via Wikimedia Commons",
    "Puy de Mur vu de Dallet — Pierre André Leclercq, CC BY-SA 4.0, via Wikimedia Commons",
    "Lussat, carte postale (1910) — anonyme, CC0, Bibliothèque Clermont Auvergne Métropole, via Wikimedia Commons",
    "Galerie de la mine des Rois — Vincent Duseigne, CC BY 2.5, via Wikimedia Commons",
    "# Musique",
    "[à compléter]",
    "# Sources",
    "E. Mallard, Bulletin de la Société française de Minéralogie, t. 13 (1890)",
    "Le Règne Minéral, numéro spécial lussatite (2015)",
    "Mindat · Encyclopaedia Britannica",
]

MOTS_CLES = ["lussatite", "Mallard", "opales-CT", "pépérites", "Helix", "ramondi", "Brésil", "bitume"]


# version : (fichier audio, horodatage des mots, crédit de la voix au générique)
VERSIONS = {
    "maquette": ("exports/_travail/voix_guide.mp3", "exports/_travail/voix_guide_mots.json",
                 "Texte et montage : jeremineralogie|Voix provisoire : synthèse vocale"),
    "synthese": ("exports/_travail/voix_synthese.wav", "exports/_travail/voix_synthese_mots.json",
                 "Texte et montage : jeremineralogie|Voix : synthèse vocale Microsoft (voix\u00a0«\u00a0Rémy\u00a0»)"),
    "finale": ("sources/voix_off.wav", "exports/_travail/voix_off_mots.json",
               "Texte, voix et montage : jeremineralogie"),
}


def projet(version):
    audio, mots, credit_voix = VERSIONS[version]
    return Projet(
        nom=f"lussatite_v1_{version}_9x16",
        dossier=ICI,
        texte_voix=ICI / "voix_off.txt",
        audio_voix=ICI / audio,
        mots=ICI / mots,
        plans=PLANS,
        generique=[l for ligne in GENERIQUE for l in ligne.format(credit_voix=credit_voix).split("|")],
        logo="LOGO_jeremineralogie.jpg",
        mots_cles=MOTS_CLES,
    )


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "maquette"
    if len(sys.argv) > 2:
        temps = [float(t) for t in sys.argv[2].split(",")]
        print(rendre(projet(version), apercu=temps))
    else:
        print(rendre(projet(version)))
