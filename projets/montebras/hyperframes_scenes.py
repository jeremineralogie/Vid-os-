"""Séquences HyperFrames de la vidéo Montebras : frises, tonnage, métaux rares, fiches chimiques, final.

Chaque séquence est composée à la durée exacte de son plan (fondus compris), calée sur les mots
du texte, puis rendue en MP4 dans sources/hf/ (non versionné).

python3 projets/montebras/hyperframes_scenes.py              -> compose et rend tout
python3 projets/montebras/hyperframes_scenes.py fiche_quartz -> une seule séquence
python3 projets/montebras/hyperframes_scenes.py --check      -> compose et vérifie sans rendre

Faits affichés (vérifiés, voir RECHERCHES_CREUSE.md et SOURCES.md) :
- formules : quartz SiO2 ; fluorapatite Ca5(PO4)3F ; fluorite CaF2 ;
  turquoise CuAl6(PO4)4(OH)8·4H2O ; wavellite Al3(PO4)2(OH,F)3·5H2O
- duretés Mohs : 7 ; 5 ; 4 ; 5 à 6 ; 3,5 à 4 — systèmes : trigonal, hexagonal, cubique, triclinique, orthorhombique
- numéros atomiques : Li 3, Nb 41, Sn 50, Ta 73, W 74
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
sys.path.insert(0, str(ICI))
import montage  # noqa: E402
import montage_projet  # noqa: E402

VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
SORTIE = ICI / "sources" / "hf"

CSS = """
:root { --fond-haut:#0b0710; --fond-bas:#1a0f2a; --violet:#7b2cbf; --violet-clair:#c77dff; --gris:#b9b3c6; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--fond-haut); }
#root { position:relative; width:100%; height:100%; font-family:"Montserrat", sans-serif; color:#fff; }
#fond { position:absolute; inset:0;
  background: radial-gradient(900px 700px at 50% 34%, rgba(123,44,191,0.22), rgba(0,0,0,0) 70%),
              linear-gradient(180deg, var(--fond-haut), var(--fond-bas)); }
/* zone utile : x 110-970, y 250-1120 (au-dessus des sous-titres, hors marges des réseaux) */
.tete { position:absolute; top:250px; left:110px; width:860px; text-align:center; }
.surtitre { font-size:30px; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:var(--violet-clair); }
.titre { margin-top:14px; font-size:80px; font-weight:800; letter-spacing:-0.01em; }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
"""

ELEMENTS = {  # symbole : nom français
    "Si": "silicium", "O": "oxygène", "Ca": "calcium", "P": "phosphore", "F": "fluor",
    "Cu": "cuivre", "Al": "aluminium", "H": "hydrogène",
}

FICHES = {
    "quartz": dict(nom="Quartz", formule="SiO<sub>2</sub>", taille=150,
                   famille="Silice · dioxyde de silicium", systeme="Système trigonal",
                   elements=["Si", "O"], durete=(7, 7), durete_txt="7"),
    "apatite": dict(nom="Apatite", formule="Ca<sub>5</sub>(PO<sub>4</sub>)<sub>3</sub>F", taille=120,
                    famille="Fluorapatite · phosphate de calcium", systeme="Ici riche en manganèse",
                    elements=["Ca", "P", "O", "F"], durete=(5, 5), durete_txt="5"),
    "fluorite": dict(nom="Fluorite", formule="CaF<sub>2</sub>", taille=150,
                     famille="Fluorure de calcium", systeme="Système cubique",
                     elements=["Ca", "F"], durete=(4, 4), durete_txt="4"),
    "turquoise": dict(nom="Turquoise", formule="CuAl<sub>6</sub>(PO<sub>4</sub>)<sub>4</sub>(OH)<sub>8</sub>·4H<sub>2</sub>O",
                      taille=60, famille="Phosphate hydraté de cuivre et d'aluminium", systeme="Système triclinique",
                      elements=["Cu", "Al", "P", "O", "H"], durete=(5, 6), durete_txt="5 à 6"),
    "wavellite": dict(nom="Wavellite", formule="Al<sub>3</sub>(PO<sub>4</sub>)<sub>2</sub>(OH,F)<sub>3</sub>·5H<sub>2</sub>O",
                      taille=64, famille="Phosphate hydraté d'aluminium", systeme="Système orthorhombique",
                      elements=["Al", "P", "O", "H", "F"], durete=(3.5, 4), durete_txt="3,5 à 4"),
}


def page(duree, corps, css, script):
    return f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}{css}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duree:.2f}" data-width="1080" data-height="1920">
      <div id="fond" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1"></div>
      <div id="scene" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="1" style="z-index:2">
{corps}
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // lente avancée de caméra sur toute la séquence
      tl.fromTo("#scene", {{ scale: 1 }}, {{ scale: 1.035, duration: {duree:.2f}, ease: "none" }}, 0);
{script}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def tete(surtitre, titre):
    return f"""        <div class="tete" id="tete"><div class="surtitre">{surtitre}</div><div class="titre">{titre}</div><div class="filet"></div></div>"""


ENTREE_TETE = '      tl.fromTo("#tete", { opacity: 0, y: -26 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, 0.15);\n'


# ---------------------------------------------------------------- frise chronologique

ETAPES = [("Antiquité", "Étain extrait, selon les sources"),
          ("1858", "Redécouverte par F.-E. Mallard"),
          ("1868 – 1914", "Exploitation de l'étain"),
          ("1965", "Carrière de feldspath")]

CSS_FRISE = """
#axe { position:absolute; left:214px; top:520px; width:6px; height:560px; border-radius:3px; background:rgba(255,255,255,0.12); }
#axe-plein { position:absolute; inset:0; border-radius:3px; background:linear-gradient(180deg, var(--violet-clair), var(--violet)); transform-origin:top center; }
.etape { position:absolute; left:190px; width:780px; height:120px; }
.point { position:absolute; left:0; top:20px; width:54px; height:54px; border-radius:50%; background:var(--fond-haut);
  border:6px solid var(--violet-clair); box-shadow:0 0 26px rgba(199,125,255,0.55); }
.annee { position:absolute; left:92px; top:0; font-size:60px; font-weight:800; white-space:nowrap; }
.legende { position:absolute; left:94px; top:76px; font-size:34px; font-weight:500; color:var(--gris); white-space:nowrap; }
"""


def frise(duree, visibles, apparitions):
    """visibles : nombre d'étapes déjà affichées au début ; apparitions : {index: instant} des suivantes."""
    ys = [520, 680, 840, 1000]
    corps = [tete("Montebras", "Histoire de la mine"),
             '        <div id="axe"><div id="axe-plein"></div></div>']
    script = [ENTREE_TETE]
    for i, (annee, legende) in enumerate(ETAPES):
        if i >= visibles and i not in apparitions:
            continue
        corps.append(f'        <div class="etape" id="e{i}" style="top:{ys[i] - 20}px"><div class="point"></div>'
                     f'<div class="annee">{annee}</div><div class="legende">{legende}</div></div>')
    dernier = max([visibles - 1] + list(apparitions))
    hauteur = lambda i: (ys[i] - 520 + 47) / 560  # noqa: E731 — axe rempli jusqu'au point i
    if visibles:
        script.append(f'      tl.fromTo("#axe-plein", {{ scaleY: 0 }}, {{ scaleY: {hauteur(visibles - 1):.3f}, duration: 0.9, ease: "power2.out" }}, 0.2);')
        for i in range(visibles):
            script.append(f'      tl.fromTo("#e{i}", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.55, ease: "power3.out" }}, {0.3 + 0.15 * i:.2f});')
    for i, t in sorted(apparitions.items()):
        script.append(f'      tl.to("#axe-plein", {{ scaleY: {hauteur(i):.3f}, duration: 0.7, ease: "power2.inOut" }}, {max(t - 0.35, 0.2):.2f});')
        script.append(f'      tl.fromTo("#e{i}", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }}, {t:.2f});')
        script.append(f'      tl.fromTo("#e{i} .point", {{ scale: 0.4 }}, {{ scale: 1, duration: 0.5, ease: "back.out(2)" }}, {t:.2f});')
    if not visibles:
        script.insert(1, '      tl.set("#axe-plein", { scaleY: 0 }, 0);')
    script.append(f'      tl.to("#axe-plein", {{ scaleY: {hauteur(dernier):.3f}, duration: 0.01 }}, {duree - 0.05:.2f});')
    return page(duree, "\n".join(corps), CSS_FRISE, "\n".join(script))


# ---------------------------------------------------------------- tonnage d'étain

CSS_ETAIN = """
#mesure { position:absolute; top:520px; left:110px; width:860px; text-align:center; }
#environ { font-size:40px; font-weight:600; color:var(--gris); }
#nombre { font-size:230px; font-weight:800; line-height:1; color:var(--violet-clair); font-variant-numeric:tabular-nums; letter-spacing:-0.03em; }
#unite { margin-top:6px; font-size:54px; font-weight:700; }
#periode { position:absolute; top:960px; left:150px; width:780px; }
#barre { position:relative; height:22px; border-radius:11px; background:rgba(255,255,255,0.12); overflow:hidden; }
#barre-plein { position:absolute; inset:0; border-radius:11px; background:linear-gradient(90deg, var(--violet), var(--violet-clair)); transform-origin:left center; }
#bornes { display:flex; justify-content:space-between; margin-top:16px; font-size:36px; font-weight:700; color:var(--gris); }
"""


def etain(duree):
    corps = "\n".join([
        tete("Montebras", "Étain extrait"),
        '        <div id="mesure"><div id="environ">environ</div><div id="nombre">0</div><div id="unite">tonnes d\'étain</div></div>',
        '        <div id="periode"><div id="barre"><div id="barre-plein"></div></div><div id="bornes"><span>1868</span><span>1914</span></div></div>',
    ])
    course = min(2.6, duree - 1.6)
    script = ENTREE_TETE + f"""
      tl.fromTo("#mesure", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 0.35);
      tl.fromTo("#periode", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 0.55);
      const compte = {{ v: 0 }};
      tl.fromTo(compte, {{ v: 0 }}, {{ v: 300, duration: {course:.2f}, ease: "power2.out",
        onUpdate: () => {{ document.getElementById("nombre").textContent = Math.round(compte.v); }} }}, 0.7);
      tl.fromTo("#barre-plein", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {course:.2f}, ease: "power2.out" }}, 0.7);
      tl.fromTo("#nombre", {{ scale: 1 }}, {{ scale: 1.06, duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1 }}, {0.7 + course:.2f});
"""
    return page(duree, corps, CSS_ETAIN, script)


# ---------------------------------------------------------------- métaux rares

METAUX = [("Sn", 50, "Étain"), ("Li", 3, "Lithium"), ("Nb", 41, "Niobium"), ("Ta", 73, "Tantale"), ("W", 74, "Tungstène")]

CSS_METAUX = """
.case { position:absolute; width:250px; height:270px; border-radius:26px; background:rgba(123,44,191,0.16);
  border:3px solid rgba(199,125,255,0.65); box-shadow:0 18px 40px rgba(0,0,0,0.45); }
.z { position:absolute; top:18px; left:22px; font-size:32px; font-weight:600; color:var(--gris); }
.sym { position:absolute; top:58px; width:100%; text-align:center; font-size:110px; font-weight:800; color:var(--violet-clair); }
.nom { position:absolute; bottom:22px; width:100%; text-align:center; font-size:34px; font-weight:600; }
"""


def metaux(duree, instants):
    positions = [(125, 520), (415, 520), (705, 520), (270, 830), (560, 830)]
    corps = [tete("Le granite de Montebras", "Métaux rares")]
    script = [ENTREE_TETE]
    for i, ((sym, z, nom), (x, y), t) in enumerate(zip(METAUX, positions, instants)):
        corps.append(f'        <div class="case" id="m{i}" style="left:{x}px;top:{y}px"><div class="z">{z}</div>'
                     f'<div class="sym">{sym}</div><div class="nom">{nom}</div></div>')
        script.append(f'      tl.fromTo("#m{i}", {{ opacity: 0, scale: 0.7, y: 24 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.8)" }}, {t:.2f});')
    return page(duree, "\n".join(corps), CSS_METAUX, "\n".join(script))


# ---------------------------------------------------------------- fiches chimiques

CSS_FICHE = """
#formule { position:absolute; top:520px; left:110px; width:860px; height:190px; display:flex; align-items:center; justify-content:center;
  border-radius:30px; background:rgba(255,255,255,0.05); border:2px solid rgba(199,125,255,0.45); }
#formule-txt { font-weight:700; white-space:nowrap; letter-spacing:0.01em; }
#formule-txt sub { font-size:0.55em; vertical-align:-0.25em; }
#famille { position:absolute; top:730px; left:110px; width:860px; text-align:center; font-size:36px; font-weight:600; color:var(--gris); }
#systeme { position:absolute; top:782px; left:110px; width:860px; text-align:center; font-size:32px; font-weight:500; color:var(--violet-clair); }
#elements { position:absolute; top:860px; left:110px; width:860px; display:flex; justify-content:center; gap:22px; }
.el { width:150px; text-align:center; }
.rond { width:104px; height:104px; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:46px; font-weight:800; background:var(--violet); box-shadow:0 0 24px rgba(123,44,191,0.6); }
.el-nom { margin-top:10px; font-size:28px; font-weight:600; color:var(--gris); }
#mohs { position:absolute; top:1040px; left:150px; width:780px; }
#mohs-titre { display:flex; justify-content:space-between; font-size:30px; font-weight:600; color:var(--gris); margin-bottom:12px; }
#mohs-titre b { color:#fff; font-weight:800; }
#graduation { position:relative; height:18px; border-radius:9px; background:rgba(255,255,255,0.12); overflow:hidden; }
#graduation-plein { position:absolute; left:0; top:0; height:100%; border-radius:9px; background:linear-gradient(90deg, var(--violet), var(--violet-clair)); transform-origin:left center; }
"""


def fiche(duree, cle):
    f = FICHES[cle]
    els = "".join(f'<div class="el"><div class="rond">{s}</div><div class="el-nom">{ELEMENTS[s]}</div></div>' for s in f["elements"])
    lo, hi = f["durete"]
    corps = "\n".join([
        tete("Composition", f["nom"]),
        f'        <div id="formule"><div id="formule-txt" style="font-size:{f["taille"]}px">{f["formule"]}</div></div>',
        f'        <div id="famille">{f["famille"]}</div>',
        f'        <div id="systeme">{f["systeme"]}</div>',
        f'        <div id="elements">{els}</div>',
        f'        <div id="mohs"><div id="mohs-titre"><span>Dureté (échelle de Mohs, 1 à 10)</span><b>{f["durete_txt"]}</b></div>'
        f'<div id="graduation"><div id="graduation-plein" style="width:{hi * 10:.0f}%"></div></div></div>',
    ])
    # échelle : la barre se remplit jusqu'à la dureté maximale de la fourchette
    script = [ENTREE_TETE,
              '      tl.fromTo("#formule", { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }, 0.45);',
              '      tl.fromTo("#formule-txt", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.9, ease: "power2.inOut" }, 0.6);',
              '      tl.fromTo("#famille", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, 1.25);',
              '      tl.fromTo("#systeme", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, 1.45);']
    for i in range(len(f["elements"])):
        script.append(f'      tl.fromTo("#elements .el:nth-child({i + 1})", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2)" }}, {1.7 + 0.14 * i:.2f});')
    t = 1.9 + 0.14 * len(f["elements"])
    script.append(f'      tl.fromTo("#mohs", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t:.2f});')
    script.append(f'      tl.fromTo("#graduation-plein", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.0, ease: "power2.out" }}, {t + 0.2:.2f});')
    if lo != hi:
        script.append(f'      tl.fromTo("#graduation-plein", {{ opacity: 1 }}, {{ opacity: 0.75, duration: 0.3, yoyo: true, repeat: 1 }}, {t + 1.25:.2f});')
    return page(duree, corps, CSS_FICHE, "\n".join(script))


# ---------------------------------------------------------------- final

FINAL = [("photo_03_quartz.jpg", "Quartz", (0.5, 0.42)), ("photo_06_apatite.jpg", "Apatite", (0.55, 0.42)),
         ("photo_08_fluorite.jpg", "Fluorite", (0.45, 0.4)), ("photo_10_turquoise.jpg", "Turquoise", (0.62, 0.32)),
         ("photo_12_wavellite_sur_turquoise.jpg", "Wavellite", (0.4, 0.62))]

CSS_FINAL = """
.vignette { position:absolute; width:250px; text-align:center; }
.vignette img { width:250px; height:250px; object-fit:cover; border-radius:26px; box-shadow:0 18px 40px rgba(0,0,0,0.5);
  border:3px solid rgba(199,125,255,0.5); }
.vignette div { margin-top:12px; font-size:32px; font-weight:700; }
"""


def final(duree, assets):
    positions = [(125, 500), (415, 500), (705, 500), (270, 830), (560, 830)]
    corps = [tete("Collection jeremineralogie", "Montebras")]
    script = [ENTREE_TETE]
    for i, ((fichier, nom, _), (x, y)) in enumerate(zip(FINAL, positions)):
        corps.append(f'        <div class="vignette" id="v{i}" style="left:{x}px;top:{y}px"><img src="assets/{Path(fichier).stem}.jpg" alt="" /><div>{nom}</div></div>')
        script.append(f'      tl.fromTo("#v{i}", {{ opacity: 0, y: 30, scale: 0.9 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "power3.out" }}, {0.35 + 0.15 * i:.2f});')
    for fichier, _, (cx, cy) in FINAL:  # vignettes carrées, recadrées sur le détail
        img = Image.open(ICI / "sources" / fichier).convert("RGB")
        w, h = img.size
        c = min(w, h) * 0.62
        x0 = min(max(cx * w - c / 2, 0), w - c)
        y0 = min(max(cy * h - c / 2, 0), h - c)
        img.crop((int(x0), int(y0), int(x0 + c), int(y0 + c))).resize((500, 500), Image.LANCZOS).save(assets / f"{Path(fichier).stem}.jpg", quality=92)
    return page(duree, "\n".join(corps), CSS_FINAL, "\n".join(script))


# ---------------------------------------------------------------- assemblage

def instant(alignes, mots, apres=0.0):
    """Horaire du premier mot de la suite `mots` dans le texte, après `apres`."""
    cible = [montage._normaliser(m) for m in mots.split()]
    texte = [montage._normaliser(j) for j, _ in alignes]
    for i in range(len(texte) - len(cible) + 1):
        if texte[i:i + len(cible)] == cible and alignes[i][1][0] >= apres:
            return alignes[i][1][0]
    raise ValueError(mots)


def composer():
    projet = montage_projet.projet()
    plages, alignes = montage.plages(projet)
    scenes = {}
    for plan, (a, b) in zip(projet.plans, plages):
        if plan.mode == "video":
            scenes[Path(plan.image).stem] = (a, b - a)
    pages = {}
    a, d = scenes["frise_debut"]
    pages["frise_debut"] = frise(d, 1, {1: instant(alignes, "Vers 1858") - a})
    a, d = scenes["frise_fin"]
    pages["frise_fin"] = frise(d, 3, {3: 1.45})
    pages["etain_300t"] = etain(scenes["etain_300t"][1])
    a, d = scenes["metaux_rares"]
    pages["metaux_rares"] = metaux(d, [instant(alignes, m, a) - a for m in ("étain,", "lithium,", "niobium,", "tantale", "tungstène.")])
    for cle in FICHES:
        pages[f"fiche_{cle}"] = fiche(scenes[f"fiche_{cle}"][1], cle)
    pages["final"] = None
    for nom, html in pages.items():
        d = DOSSIER / nom
        d.mkdir(parents=True, exist_ok=True)
        (d / "assets").mkdir(exist_ok=True)
        if nom == "final":
            html = final(scenes["final"][1], d / "assets")
        (d / "index.html").write_text(html, encoding="utf-8")
        (d / "meta.json").write_text(json.dumps({"id": nom, "name": nom}), encoding="utf-8")
        (d / "package.json").write_text(json.dumps({"name": nom, "private": True, "type": "module"}), encoding="utf-8")
    return scenes


def rendre(noms):
    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom in noms:
        subprocess.run(["npx", "--yes", VERSION, "render", str(DOSSIER / nom), "-q", "delivery", "--fps", "30",
                        "-o", str(SORTIE / f"{nom}.mp4"), "--quiet"], check=True)
        print("rendu :", nom)


if __name__ == "__main__":
    scenes = composer()
    if "--check" in sys.argv:
        for nom in scenes:
            subprocess.run(["npx", "--yes", VERSION, "check", str(DOSSIER / nom)])
    else:
        demandes = [a for a in sys.argv[1:] if not a.startswith("-")]
        rendre(demandes or list(scenes))
