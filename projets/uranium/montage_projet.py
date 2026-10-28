"""L'uranium français — découpage. Vidéo muette, sous-titres karaoké (rythme un peu plus rapide).

Séquences chiffrées, fiches chimiques et prudence : HyperFrames (python3 projets/uranium/hyperframes_scenes.py)

python3 projets/uranium/montage_projet.py            -> vidéo
python3 projets/uranium/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
import montage  # noqa: E402
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402

# photos claires : voile plus dense sous les sous-titres karaoké
montage.VOILE_FORCE = 0.68
montage.VOILE_SOUS_TITRES = montage._voile_sous_titres()


def hf(nom, debut_sur):
    return Plan(f"hf/{nom}.mp4", debut_sur, "video")


def photo(n, debut_sur, titre, depart, arrivee, coupe=False):
    return Plan(f"photo_{n:02d}.jpg", debut_sur, depart=depart, arrivee=arrivee,
                titres=[(titre, 0.04, 0.96)] if titre else [], coupe_franche=coupe)


PLANS = [
    photo(3, "L'uranium français", "L'uranium français", (0.5, 0.5, 1.0), (0.45, 0.45, 1.35)),
    hf("cea_1945", "Dès 1945"),
    Plan("arch_puits_henriette_1955.png", "Le 25 novembre", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.62, 0.5, 1.25),
         titres=[("La Crouzille, 1948", 0.05, 0.95)]),
    Plan("arch_carte_centres_1955.png", "En 1955, la France", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.48, 0.5, 1.12),
         titres=[("Les centres en 1955", 0.05, 0.95)]),
    hf("france_bilan", "Au total"),
    # Margnac
    photo(2, "L'un des géants", "Margnac", (0.5, 0.55, 1.0), (0.5, 0.6, 1.3)),
    hf("margnac_tonnage", "De 1953 à 1995"),
    Plan("arch_margnac_bloc_1958.png", "En 1958, un rapport", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.48, 0.42, 1.3),
         titres=[("Margnac, 1958", 0.05, 0.95)]),
    hf("trois_mineraux", "Trois minéraux"),
    hf("fiche_sabugalite", "La sabugalite est"),
    photo(1, "À Margnac, elle forme", "Sabugalite · Margnac", (0.55, 0.45, 1.0), (0.6, 0.4, 1.5)),
    hf("fiche_autunite", "L'autunite est un phosphate"),
    photo(4, "Sous ultraviolet, elle brille", "Autunite · Margnac", (0.4, 0.4, 1.0), (0.4, 0.35, 1.4)),
    hf("fiche_uranophane", "L'uranophane, un silicate"),
    photo(5, "pousse en fines aiguilles", "Uranophane · Margnac", (0.45, 0.6, 1.0), (0.5, 0.55, 1.6)),
    photo(6, "La gummite n'est", "Gummite · Margnac", (0.5, 0.5, 1.0), (0.55, 0.4, 1.35)),
    photo(6, "Elle naît de l'altération", "Gummite · Margnac", (0.55, 0.4, 1.35), (0.6, 0.38, 1.7), coupe=True),
    # Les Oudots
    Plan("arch_carte_centres_1955.png", "Direction la Saône-et-Loire", "carte", depart=(0.5, 0.5, 1.0),
         arrivee=(0.72, 0.5, 2.0), titres=[("Les Oudots", 0.05, 0.95)]),
    hf("champeaux_1800", "Près d'Autun"),
    Plan("arch_bauzot_1955.png", "En 1950, la pechblende", "carte", depart=(0.5, 0.5, 1.0), arrivee=(0.42, 0.45, 1.2),
         titres=[("Mine de Bauzot", 0.05, 0.95)]),
    hf("oudots_tonnage", "Aux Oudots, trois"),
    hf("fiche_torbernite", "La torbernite est"),
    photo(7, "Contrairement à l'autunite", "Torbernite · Les Oudots", (0.42, 0.62, 1.3), (0.4, 0.6, 1.6)),
    # Margabal
    hf("margabal_tonnage", "Cap sur l'Aveyron"),
    photo(8, "Mais sa torbernite", "Torbernite · Margabal", (0.5, 0.52, 1.0), (0.5, 0.52, 1.45)),
    # Hyverneresse
    hf("hyverneresse_tonnage", "Retour en Creuse"),
    photo(9, "Ici, une autunite", "Autunite · Hyverneresse", (0.5, 0.5, 1.0), (0.55, 0.45, 1.5)),
    # ouraline
    photo(10, "L'uranium a aussi", "Ouraline", (0.5, 0.5, 1.0), (0.4, 0.5, 1.12)),
    hf("fiche_ouraline", "L'ouraline contient"),
    photo(10, "Sous ultraviolet, elle", "Ouraline", (0.38, 0.48, 1.25), (0.38, 0.48, 1.3)),
    photo(11, "s'illumine", "Ouraline sous UV", (0.38, 0.45, 1.3), (0.38, 0.45, 1.45)),
    # prudence et fin
    hf("prudence", "Attention"),
    photo(12, "Collection jeremineralogie", "", (0.3, 0.62, 1.7), (0.33, 0.6, 1.45)),
]

MOTS_CLES = ["uranium", "pechblende", "Margnac", "sabugalite", "autunite", "uranophane", "gummite", "Oudots",
             "torbernite", "Margabal", "Hyverneresse", "ouraline", "radioactifs"]


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    # karaoké un peu plus rapide que Montebras (0,36 s par mot + 0,9 s)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots, par_mot=0.32, base=0.75)
    return Projet(
        nom="uranium_v1_9x16",
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
