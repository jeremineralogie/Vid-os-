"""Séquences HyperFrames de « Barytes miel du Puy-de-Dôme ».

Toujours une image en fond (carte géologique, photo du minéral ou document d'archive), jamais de fond violet.
Chaque séquence est composée à la durée exacte de son plan et calée sur les mots du texte.

python3 projets/barytes/hyperframes_scenes.py               -> compose et rend tout
python3 projets/barytes/hyperframes_scenes.py carte_gisements -> une seule séquence
python3 projets/barytes/hyperframes_scenes.py --check       -> compose et vérifie sans rendre

Faits affichés : voir RECHERCHES.md et SOURCES.md.
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
sys.path.insert(0, str(ICI))
import montage  # noqa: E402
import montage_projet  # noqa: E402

VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
SORTIE = ICI / "sources" / "hf"
SRC = ICI / "sources"

CSS = """
:root { --violet:#7b2cbf; --violet-clair:#c77dff; --gris:#d6d0e0; --miel:#f2b544; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#000; }
#root { position:relative; width:100%; height:100%; font-family:"Montserrat", sans-serif; color:#fff; }
#photo { position:absolute; inset:0; overflow:hidden; }
#photo img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(0.5) saturate(1.05); }
#photo-voile { position:absolute; inset:0;
  background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.12) 30%, rgba(0,0,0,0.22) 60%, rgba(0,0,0,0.75) 100%); }
/* zone utile : x 110-970, y 250-1120 (au-dessus des sous-titres, hors marges des réseaux) */
.tete { position:absolute; top:250px; left:110px; width:860px; text-align:center; }
.surtitre { font-size:30px; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:var(--violet-clair);
  text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.titre { margin-top:14px; font-size:80px; font-weight:800; letter-spacing:-0.01em; text-shadow:0 4px 18px rgba(0,0,0,0.7); }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
.grand { font-weight:800; line-height:1; color:var(--miel); font-variant-numeric:tabular-nums; letter-spacing:-0.03em;
  text-shadow:0 6px 24px rgba(0,0,0,0.6); }
.unite { font-size:46px; font-weight:700; text-shadow:0 3px 14px rgba(0,0,0,0.8); }
.petit { font-size:34px; font-weight:600; color:var(--gris); text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.badge { display:inline-block; padding:12px 26px; border-radius:40px; font-size:32px; font-weight:700;
  background:rgba(0,0,0,0.55); border:2px solid rgba(199,125,255,0.75); }
.panneau { background:rgba(8,6,12,0.66); border:2px solid rgba(199,125,255,0.55); border-radius:34px;
  box-shadow:0 24px 60px rgba(0,0,0,0.55); }
"""


def page(duree, corps, css, script, fond="assets/fond.jpg"):
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
      <div id="photo" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1"><img id="photo-img" src="{fond}" alt="" /><div id="photo-voile"></div></div>
      <div id="scene" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="1" style="z-index:2">
{corps}
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#photo-img", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {duree:.2f}, ease: "none" }}, 0);
{script}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def tete(surtitre, titre):
    return f'        <div class="tete" id="tete"><div class="surtitre">{surtitre}</div><div class="titre">{titre}</div><div class="filet"></div></div>'


ENTREE_TETE = '      tl.fromTo("#tete", { opacity: 0, y: -26 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, 0.15);\n'


def apparition(sel, t, dy=24, d=0.55):
    return f'      tl.fromTo("{sel}", {{ opacity: 0, y: {dy} }}, {{ opacity: 1, y: 0, duration: {d}, ease: "power3.out" }}, {t:.2f});'


def compteur(sel, depart, arrivee, t, d, decimales=0, separateur=False, prefixe="", suffixe=""):
    """Compteur animé, au format français (virgule décimale)."""
    var = sel.strip("#").replace("-", "_")
    fmt = ("v.toFixed(%d).replace('.', ',')" % decimales) if decimales else "Math.round(v).toString()"
    milliers = ".replace(/\\B(?=(\\d{3})+(?!\\d))/g, '\\u202f')" if separateur else ""
    return f"""      const {var} = {{ v: {depart} }};
      tl.fromTo({var}, {{ v: {depart} }}, {{ v: {arrivee}, duration: {d:.2f}, ease: "power2.out",
        onUpdate: () => {{ const v = {var}.v; document.querySelector("{sel}").textContent = "{prefixe}" + {fmt}{milliers} + "{suffixe}"; }} }}, {t:.2f});"""


def preparer_fond(source, assets, flou=False, nom="fond.jpg"):
    img = Image.open(source).convert("RGB")
    w, h = img.size  # recadrage 9:16 centré
    cw = min(w, h * 9 / 16)
    ch = cw * 16 / 9
    img = img.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2))).resize((1080, 1920), Image.LANCZOS)
    if flou:
        img = img.filter(ImageFilter.GaussianBlur(14))
    img.save(assets / nom, quality=90)


# ---------------------------------------------------------------- carte des gisements

# commune (jamais l'emplacement précis du gisement), photo de l'auteur, côté de l'étiquette
GISEMENTS = [
    ("Châtel-Guyon", "Châtel-Guyon", 45.9227, 3.0659, "photo_11.jpg", "g"),
    ("Royat", "puy Chateix", 45.7666, 3.0506, "photo_03.jpg", "g"),
    ("Saint-Saturnin", "Côte d'Abot", 45.6597, 3.0930, "photo_08.jpg", "d"),
    ("Olloix", "Le Liauzun", 45.6222, 3.0455, "photo_06.jpg", "g"),
    ("Champeix", "Champeix", 45.5881, 3.1286, "photo_09.jpg", "d"),
    ("Saint-Babel", "Saint-Babel", 45.5974, 3.3017, "photo_01.jpg", "d"),
]
R = 6378137


def _merc(lon, lat):
    return math.radians(lon) * R, R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def carte_gisements(duree, instants, assets):
    """Département entier, zoom sur les gisements, puis un point et une photo par gisement."""
    cadre = json.loads((SRC / "carte" / "cadre.json").read_text())
    x0, y0, x1, y1 = cadre["bbox"]

    def px(lon, lat):
        x, y = _merc(lon, lat)
        return (x - x0) / (x1 - x0) * 1080, (y1 - y) / (y1 - y0) * 1920

    shutil.copy(SRC / "carte" / "base_SCAN_F_GEOL1M.png", assets / "carte.png")
    contour = json.loads((SRC / "carte" / "dep63.geojson").read_text())["features"][0]["geometry"]
    polys = contour["coordinates"] if contour["type"] == "MultiPolygon" else [contour["coordinates"]]
    chemin = " ".join("M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in (px(*p) for p in ring[::4])) + " Z"
                      for poly in polys for ring in poly[:1])
    # zoom : le groupe de gisements centré vers (540, 760), échelle s
    pts = [px(lo, la) for _, _, la, lo, _, _ in GISEMENTS]
    gx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    gy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
    s = 2.2
    tx, ty = 540 - gx * s, 770 - gy * s
    ecran = [(p[0] * s + tx, p[1] * s + ty) for p in pts]
    corps = [f'        <div id="monde" style="position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0">'
             '<img src="assets/carte.png" style="position:absolute;inset:0;width:1080px;height:1920px;filter:brightness(0.62) saturate(0.95)"/>'
             '<svg width="1080" height="1920" style="position:absolute;inset:0">'
             f'<path d="M0,0 H1080 V1920 H0 Z {chemin}" fill="rgba(0,0,0,0.6)" fill-rule="evenodd"/>'
             f'<path id="contour" d="{chemin}" fill="none" stroke="#c77dff" stroke-width="3" stroke-linejoin="round"/></svg></div>',
             '        <div id="voile-haut" style="position:absolute;left:0;top:0;width:1080px;height:480px;'
             'background:linear-gradient(180deg,rgba(0,0,0,0.75),rgba(0,0,0,0))"></div>',
             tete("Puy-de-Dôme", "Barytes miel")]
    # vignettes en deux colonnes, rangées dans l'ordre vertical des points pour que les traits ne se croisent pas
    fentes = {}
    for col, xc, ys in (("g", 235, (510, 750, 990)), ("d", 845, (500, 760, 1000))):
        idx = sorted((i for i, g in enumerate(GISEMENTS) if g[5] == col), key=lambda i: ecran[i][1])
        for i, y in zip(idx, ys):
            fentes[i] = (xc, y)
    script = [ENTREE_TETE,
              '      tl.fromTo("#contour", { strokeDasharray: 6000, strokeDashoffset: 6000 }, { strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut" }, 0.1);',
              f'      tl.to("#monde", {{ x: {tx:.1f}, y: {ty:.1f}, scale: {s}, duration: 1.5, ease: "power2.inOut" }}, 1.0);']
    lignes = []
    for i, ((nom, lieu, _, _, ph, _), (ex, ey), t) in enumerate(zip(GISEMENTS, ecran, instants)):
        shutil.copy(SRC / ph, assets / ph)
        fx, fy = fentes[i]
        t = max(t, 2.5 + 0.2 * i)
        lignes.append(f'<line id="l{i}" x1="{ex:.1f}" y1="{ey:.1f}" x2="{fx}" y2="{fy}" stroke="rgba(255,255,255,0.85)" stroke-width="3"/>')
        corps.append(f'        <div id="p{i}" style="position:absolute;left:{ex - 13:.1f}px;top:{ey - 13:.1f}px;width:26px;height:26px;border-radius:50%;'
                     'background:#f2b544;border:4px solid #fff;box-shadow:0 0 18px rgba(242,181,68,0.9)"></div>')
        sous = f'<div style="display:inline-block;margin-top:4px;padding:2px 12px;border-radius:14px;background:rgba(0,0,0,0.7);font-size:24px;font-weight:700;color:#fff">{lieu}</div>' if lieu != nom else ""
        corps.append(f'        <div id="v{i}" style="position:absolute;left:{fx - 130}px;top:{fy - 75}px;width:260px;text-align:center">'
                     f'<div style="width:150px;height:150px;margin:0 auto;border-radius:50%;overflow:hidden;border:5px solid #f2b544;'
                     f'box-shadow:0 10px 30px rgba(0,0,0,0.7)"><img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>'
                     f'<div style="margin-top:8px;font-size:30px;font-weight:800;text-shadow:0 2px 10px rgba(0,0,0,0.9);white-space:nowrap">{nom}</div>{sous}</div>')
        script += [f'      tl.fromTo("#p{i}", {{ opacity: 0, scale: 0 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(3)" }}, {t:.2f});',
                   f'      tl.fromTo("#l{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t + 0.1:.2f});',
                   f'      tl.fromTo("#v{i}", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {t + 0.12:.2f});']
    corps.insert(3, '        <svg width="1080" height="1920" style="position:absolute;inset:0">' + "".join(lignes) + '</svg>')
    preparer_fond(SRC / "carte" / "base_SCAN_F_GEOL1M.png", assets)
    return page(duree, "\n".join(corps), "", "\n".join(script))


# ---------------------------------------------------------------- fiche de la baryte (photo du minéral en fond)

CSS_FICHE = """
#carte { position:absolute; top:470px; left:90px; width:900px; padding:40px 30px 36px; }
#formule { text-align:center; font-weight:800; font-size:110px; white-space:nowrap; }
#formule sub { font-size:0.55em; vertical-align:-0.25em; }
#nom-chimique { margin-top:10px; text-align:center; font-size:34px; font-weight:600; color:var(--miel); }
#elements { margin-top:30px; display:flex; justify-content:center; gap:30px; }
.el { width:160px; text-align:center; }
.rond { width:104px; height:104px; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:44px; font-weight:800; background:var(--violet); box-shadow:0 0 24px rgba(123,44,191,0.6); }
.rond.ba { background:#5a3d08; border:3px solid var(--miel); color:var(--miel); box-shadow:0 0 26px rgba(242,181,68,0.6); }
.el-nom { margin-top:10px; font-size:27px; font-weight:600; color:var(--gris); }
#mesures { margin-top:34px; display:flex; gap:24px; padding:0 20px; }
.mesure { flex:1; text-align:center; padding:18px 10px; border-radius:24px; background:rgba(255,255,255,0.06); }
.mesure .grand { font-size:84px; }
"""


def fiche_baryte(duree, t_densite, assets):
    preparer_fond(SRC / "photo_11.jpg", assets)
    corps = "\n".join([
        tete("Composition", "La baryte"),
        '        <div id="carte" class="panneau"><div id="formule">BaSO<sub>4</sub></div>'
        '<div id="nom-chimique">Sulfate de baryum</div>'
        '<div id="elements"><div class="el"><div class="rond ba">Ba</div><div class="el-nom">baryum</div></div>'
        '<div class="el"><div class="rond">S</div><div class="el-nom">soufre</div></div>'
        '<div class="el"><div class="rond">O</div><div class="el-nom">oxygène</div></div></div>'
        '<div id="mesures"><div class="mesure" id="m-densite"><div id="densite" class="grand">0</div><div class="petit">densité</div></div>'
        '<div class="mesure" id="m-durete"><div class="grand" style="white-space:nowrap">3 à 3,5</div><div class="petit">dureté (Mohs)</div></div></div></div>',
    ])
    script = [ENTREE_TETE,
              '      tl.fromTo("#carte", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.25);',
              '      tl.fromTo("#formule", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.8, ease: "power2.inOut" }, 0.4);',
              apparition("#nom-chimique", 0.9, 12, 0.35)]
    for i in range(3):
        script.append(f'      tl.fromTo("#elements .el:nth-child({i + 1})", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }}, {1.1 + 0.1 * i:.2f});')
    t = max(1.6, t_densite - 0.2)
    script += [apparition("#m-densite", t, 14, 0.4), compteur("#densite", 0, 4.5, t + 0.1, 1.4, decimales=1),
               apparition("#m-durete", t + 0.6, 14, 0.4),
               '      tl.fromTo(".rond.ba", { boxShadow: "0 0 10px rgba(242,181,68,0.3)" }, { boxShadow: "0 0 36px rgba(242,181,68,0.9)", duration: 0.7, yoyo: true, repeat: 1, ease: "sine.inOut" }, 1.6);']
    return page(duree, corps, CSS_FICHE, "\n".join(script))


# ---------------------------------------------------------------- années et chiffres, sur leur document

def annee(duree, assets, source, surtitre, titre, depart, arrivee, legende, badge, t_badge=2.0):
    preparer_fond(source, assets)
    corps = [tete(surtitre, titre),
             f'        <div id="annee" class="grand" style="position:absolute;top:560px;width:100%;text-align:center;font-size:250px">{depart}</div>',
             f'        <div id="legende" class="petit" style="position:absolute;top:850px;left:110px;width:860px;text-align:center">{legende}</div>',
             f'        <div id="badge" style="position:absolute;top:960px;width:100%;text-align:center"><span class="badge">{badge}</span></div>']
    script = [ENTREE_TETE, apparition("#annee", 0.3, 30), compteur("#annee", depart, arrivee, 0.4, 1.6),
              apparition("#legende", 1.5), apparition("#badge", min(t_badge, duree - 1.6))]
    return page(duree, "\n".join(corps), "", "\n".join(script))


def gonnard_18(duree, assets):
    preparer_fond(SRC / "archives" / "gonnard1870_p-18.png", assets)
    noms = ["primitive", "binaire", "trapézienne", "épointée", "progressive", "octotrigésimale"]
    corps = [tete("Gonnard, 1870", "Formes de la baryte"),
             '        <div id="mesure" style="position:absolute;top:520px;width:100%;text-align:center">'
             '<div id="nombre" class="grand" style="font-size:230px">0</div><div class="unite">variétés cristallines</div></div>',
             '        <div id="noms" style="position:absolute;top:880px;left:110px;width:860px;text-align:center;line-height:1.9">' +
             " ".join(f'<span class="badge" style="font-size:28px;margin:0 6px">{n}</span>' for n in noms) + '</div>']
    script = [ENTREE_TETE, apparition("#mesure", 0.3, 30), compteur("#nombre", 0, 18, 0.4, 1.6),
              apparition("#noms", min(1.8, duree - 1.6), 14, 0.5)]
    return page(duree, "\n".join(corps), "#photo img { filter:brightness(0.28) saturate(0.9); }", "\n".join(script))


def final(duree, assets):
    photos = [f"photo_{n:02d}.jpg" for n in (1, 3, 8, 6, 9, 11, 2, 4, 7, 10, 5)]
    preparer_fond(SRC / "photo_05.jpg", assets, flou=True)
    cases = []
    for k, ph in enumerate(photos):
        shutil.copy(SRC / ph, assets / ph)
        col, lig = k % 3, k // 3
        x = 120 + col * 286 + (143 if lig == 3 else 0)
        cases.append(f'        <div class="case" id="c{k}" style="position:absolute;left:{x}px;top:{260 + lig * 215}px;width:270px;height:200px;'
                     'border-radius:22px;overflow:hidden;border:3px solid rgba(242,181,68,0.85);box-shadow:0 12px 30px rgba(0,0,0,0.6)">'
                     f'<img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>')
    script = [f'      tl.fromTo("#c{k}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.8)" }}, {0.15 + 0.12 * k:.2f});'
              for k in range(len(photos))]
    return page(duree, "\n".join(cases), "", "\n".join(script))


# ---------------------------------------------------------------- assemblage

def instant(alignes, mots, apres=0.0):
    cible = [montage._normaliser(m) for m in mots.split()]
    texte = [montage._normaliser(j) for j, _ in alignes]
    for i in range(len(texte) - len(cible) + 1):
        if texte[i:i + len(cible)] == cible and alignes[i][1][0] >= apres:
            return alignes[i][1][0]
    raise ValueError(mots)


def composer():
    projet = montage_projet.projet()
    plages, alignes = montage.plages(projet)
    scenes = {Path(p.image).stem: (a, b - a) for p, (a, b) in zip(projet.plans, plages) if p.mode == "video"}
    pages = {}

    def rel(nom, mots):
        a = scenes[nom][0]
        return instant(alignes, mots, a) - a

    for nom, (a, d) in scenes.items():
        dossier = DOSSIER / nom
        assets = dossier / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        if nom == "carte_gisements":
            mots = ["Châtel-Guyon,", "Royat,", "Saint-Saturnin,", "Olloix,", "Champeix", "Saint-Babel."]
            html = carte_gisements(d, [rel(nom, m) for m in mots], assets)
        elif nom == "fiche_baryte":
            html = fiche_baryte(d, rel(nom, "sa densité"), assets)
        elif nom == "hauy_1823":
            html = annee(d, assets, SRC / "archives" / "hauy1823_pdf127-127.png", "René Just Haüy", "Traité de minéralogie",
                         1800, 1823, "Atlas, deuxième édition", "Planches de la baryte", rel(nom, "dessine"))
        elif nom == "gonnard_1870":
            html = annee(d, assets, SRC / "archives" / "gonnard1870_couverture_recadree.png", "Ferdinand Gonnard",
                         "Minéralogie", 1850, 1870, "du département du Puy-de-Dôme", "Paris, F. Savy", rel(nom, "la Minéralogie"))
        elif nom == "gonnard_18":
            html = gonnard_18(d, assets)
        elif nom == "final":
            html = final(d, assets)
        else:
            raise ValueError(nom)
        (dossier / "index.html").write_text(html, encoding="utf-8")
        (dossier / "meta.json").write_text(json.dumps({"id": nom, "name": nom}), encoding="utf-8")
        (dossier / "package.json").write_text(json.dumps({"name": nom, "private": True, "type": "module"}), encoding="utf-8")
        pages[nom] = d
    return pages


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
            r = subprocess.run(["npx", "--yes", VERSION, "check", str(DOSSIER / nom)], capture_output=True, text=True)
            lignes = [l for l in r.stdout.splitlines() if "error(s)" in l or "Check" in l or "✗" in l]
            print(nom, " | ".join(l.strip() for l in lignes))
    else:
        demandes = [a for a in sys.argv[1:] if not a.startswith("-")]
        rendre(demandes or list(scenes))
