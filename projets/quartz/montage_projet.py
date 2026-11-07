"""Les couleurs du quartz — découpage. Vidéo sans voix ni musique (l'auteur enregistrera sa voix), sous-titres karaoké.

Les photos de la collection alternent avec des scènes réalistes (rendus Blender habillés avec HyperFrames, voir
realiste.py). Chaque scène déroule ses étapes à au moins 4 s chacune : quand la phrase lue est plus courte, le karaoké
marque une pause à la fin de la scène (voir `allonger`).

python3 projets/quartz/montage_projet.py            -> vidéo
python3 projets/quartz/montage_projet.py 1,20,60    -> aperçus PNG à ces instants
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
sys.path.insert(0, str(ICI))
import montage  # noqa: E402
from montage import Plan, Projet, mots_lecture, rendre  # noqa: E402
from realiste import NOMINAL  # noqa: E402

montage.VOILE_FORCE = 0.68
montage.VOILE_SOUS_TITRES = montage._voile_sous_titres()


def hf(nom, debut_sur):
    return Plan(f"hf/{nom}.mp4", debut_sur, "video")


def photo(n, debut_sur, titre, depart=(0.5, 0.45, 1.0), arrivee=(0.5, 0.4, 1.25)):
    return Plan(f"photo_{n:02d}.jpg", debut_sur, depart=depart, arrivee=arrivee, titres=[(titre, 0.04, 0.96)] if titre else [])


PLANS = [
    photo(6, "Les couleurs du quartz", "Les couleurs du quartz", (0.5, 0.5, 1.0), (0.5, 0.45, 1.2)),
    hf("structure_3d", "Le quartz est l’un des minéraux"),
    photo(9, "Pourtant, il peut présenter", "Cristal de roche"),
    photo(1, "au noir profond du morion", "Quartz morion"),
    photo(7, "en passant par les nuances violettes", "Améthyste"),
    photo(4, "ou les teintes brunes", "Quartz fumé"),
    photo(12, "Mais d’où viennent", "Quartz laiteux"),
    # morion
    photo(1, "Commençons par le quartz morion", "Quartz morion", (0.5, 0.45, 1.0), (0.5, 0.35, 1.4)),
    photo(2, "Cette variété très sombre", "Quartz morion"),
    photo(3, "à des phénomènes liés", "Quartz morion"),
    hf("irradiation_3d", "Au cours de son histoire"),
    hf("centre_al_3d", "Ces rayonnements modifient"),
    # quartz fumé
    photo(4, "Le quartz fumé présente", "Quartz fumé"),
    photo(5, "Sa couleur varie", "Quartz fumé"),
    hf("gamme_3d", "Là encore, l’irradiation"),
    # améthyste
    photo(6, "Passons maintenant à l’améthyste", "Améthyste"),
    photo(7, "C’est probablement l’une", "Améthyste"),
    photo(8, "grâce à ses teintes violettes", "Améthyste"),
    hf("fer_3d", "Sa coloration est principalement liée"),
    hf("absorption_3d", "C’est cette absorption sélective"),
    # quartz laiteux
    photo(11, "Le quartz blanc laiteux", "Quartz laiteux"),
    photo(12, "Contrairement aux variétés", "Quartz laiteux"),
    hf("laiteux_3d", "son apparence blanche"),
    # cristal de roche
    photo(9, "Enfin, le quartz transparent", "Cristal de roche", (0.5, 0.45, 1.0), (0.5, 0.4, 1.4)),
    hf("transparence_3d", "Sa transparence s’explique"),
    photo(10, "Il révèle alors", "Cristal de roche"),
    # conclusion
    photo(5, "Finalement, ces différentes", ""),
    hf("synthese", "La composition reste"),
    photo(6, "C’est toute la richesse", "", (0.5, 0.5, 1.0), (0.5, 0.45, 1.3)),
]

MOTS_CLES = ["quartz", "SiO₂", "morion", "améthyste", "fumé", "irradiation", "aluminium", "centres", "fer",
             "absorption", "laiteux", "inclusions", "diffusion", "cristal", "roche", "minéralogie"]


def allonger(chemin, plans, minimums, marge=0.6):
    """Décale le texte qui suit une séquence animée trop courte : la séquence dure au moins son minimum."""
    mots = json.loads(Path(chemin).read_text(encoding="utf-8"))
    norm = [montage._normaliser(m["w"]) for m in mots]
    debuts, depuis = [], 0
    for p in plans:
        cible = [c for c in (montage._normaliser(m) for m in p.debut_sur.split()) if c]
        i = next(i for i in range(depuis, len(norm)) if norm[i:i + len(cible)] == cible)
        debuts.append(i)
        depuis = i + 1
    for k, p in enumerate(plans[:-1]):
        nom = Path(p.image).stem
        if p.mode != "video" or nom not in minimums:
            continue
        a, b = debuts[k], debuts[k + 1]
        manque = minimums[nom] + marge - (mots[b]["t"] - mots[a]["t"])
        if manque > 0:
            for m in mots[b:]:
                m["t"] += manque
    Path(chemin).write_text(json.dumps(mots, ensure_ascii=False), encoding="utf-8")


def projet():
    mots = ICI / "exports/_travail/texte_ecran_mots.json"
    mots.parent.mkdir(parents=True, exist_ok=True)
    mots_lecture((ICI / "texte_ecran.txt").read_text(encoding="utf-8"), mots, par_mot=0.32, base=0.75)
    allonger(mots, PLANS, NOMINAL)
    return Projet(
        nom="quartz_v1_9x16",
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
