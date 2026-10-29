"""Séquences HyperFrames de « Minéraux de la Creuse ».

Fil conducteur : carte de la Creuse en relief (IGN, voir carte_fond.py). Pour chaque gisement, la carte dézoome depuis
le gisement précédent, le point apparaît sur la commune, la carte zoome dessus, le contour de la commune s'allume.
Montebras et Lavaveix-les-Mines ont une séquence d'archives (cartes postales anciennes) avec compteurs.
Toujours une image en fond (carte, archive), jamais de fond violet.

python3 projets/creuse/hyperframes_scenes.py               -> compose et rend tout
python3 projets/creuse/hyperframes_scenes.py carte_1       -> une seule séquence
python3 projets/creuse/hyperframes_scenes.py --check       -> compose et vérifie sans rendre

Faits affichés : voir RECHERCHES.md et SOURCES.md.
"""
import json
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
from gisements import CIBLE, GISEMENTS, VILLES, ZOOM, boite_zoom, ecran, vue_zoom  # noqa: E402

VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
SORTIE = ICI / "sources" / "hf"
SRC = ICI / "sources"
CARTE = SRC / "carte"
ARCH = SRC / "archives"

CSS = """
:root { --violet:#7b2cbf; --violet-clair:#c77dff; --gris:#d6d0e0; --or:#f2b544; }
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
.titre { margin-top:14px; font-size:80px; font-weight:800; letter-spacing:-0.01em; white-space:nowrap; text-shadow:0 4px 18px rgba(0,0,0,0.7); }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
.grand { font-weight:800; line-height:1; color:var(--or); font-variant-numeric:tabular-nums; letter-spacing:-0.02em;
  text-shadow:0 6px 24px rgba(0,0,0,0.6); white-space:nowrap; }
.petit { font-size:30px; font-weight:600; color:var(--gris); text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.panneau { background:rgba(8,6,12,0.7); border:2px solid rgba(199,125,255,0.55); border-radius:34px;
  box-shadow:0 24px 60px rgba(0,0,0,0.55); }
.archive { position:absolute; border-radius:22px; overflow:hidden; border:4px solid rgba(242,230,210,0.9);
  box-shadow:0 20px 50px rgba(0,0,0,0.7); background:#1a1520; }
.archive img { width:100%; height:100%; object-fit:contain; display:block; }
"""


def page(duree, corps, css, script, fond="assets/fond.jpg", zoom_fond=True):
    anim = f'      tl.fromTo("#photo-img", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {duree:.2f}, ease: "none" }}, 0);\n' if zoom_fond else ""
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
{anim}{script}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def tete(surtitre, titre, ident="tete"):
    taille = min(80, int(1500 / max(len(titre), 1)))
    return (f'        <div class="tete" id="{ident}"><div class="surtitre">{surtitre}</div>'
            f'<div class="titre" style="font-size:{taille}px">{titre}</div><div class="filet"></div></div>')


def entree(sel, t, dy=-26, d=0.6):
    return f'      tl.fromTo("{sel}", {{ opacity: 0, y: {dy} }}, {{ opacity: 1, y: 0, duration: {d}, ease: "power3.out" }}, {t:.2f});'


def apparition(sel, t, dy=24, d=0.55):
    return entree(sel, t, dy, d)


def compteur(sel, depart, arrivee, t, d, separateur=False):
    """Compteur animé ; séparateur des milliers : espace fine insécable."""
    var = "c_" + sel.strip("#").replace("-", "_")
    milliers = ".replace(/\\B(?=(\\d{3})+(?!\\d))/g, '\\u202f')" if separateur else ""
    return f"""      const {var} = {{ v: {depart} }};
      tl.fromTo({var}, {{ v: {depart} }}, {{ v: {arrivee}, duration: {d:.2f}, ease: "power2.out",
        onUpdate: () => {{ document.querySelector("{sel}").textContent = Math.round({var}.v).toString(){milliers}; }} }}, {t:.2f});"""


def preparer_fond(source, assets, flou=False, nom="fond.jpg"):
    img = Image.open(source).convert("RGB")
    w, h = img.size  # recadrage 9:16 centré
    cw = min(w, h * 9 / 16)
    ch = cw * 16 / 9
    img = img.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2))).resize((1080, 1920), Image.LANCZOS)
    if flou:
        img = img.filter(ImageFilter.GaussianBlur(14))
    img.save(assets / nom, quality=90)


def fmt(v):
    return f"{v:,}".replace(",", " ")


# ---------------------------------------------------------------- carte de la Creuse : dézoom, point, zoom

# séquences carte : nom -> index du gisement
CARTES = {f"carte_{i + 1}": i for i, g in enumerate(GISEMENTS) if g[6]}
# cartes postales anciennes montrées dans la séquence carte (Crozant)
CARTES_POSTALES = {0: ["C5.jpg", "C6.jpg"]}


def contour_commune(code, tol=1.2):
    """Contour de la commune en coordonnées de la vue d'ensemble (tracé simplifié, tolérance en px de zoom)."""
    d = json.loads((CARTE / "communes.geojson").read_text())
    f = next(f for f in d["features"] if f["properties"]["code_insee"] == code)
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    chemins = []
    pas = tol / ZOOM
    for poly in polys:
        pts, dernier = [], None
        for lon, lat in poly[0]:
            p = ecran(lat, lon)
            if dernier is None or abs(p[0] - dernier[0]) + abs(p[1] - dernier[1]) >= pas:
                pts.append(p)
                dernier = p
        if len(pts) > 3:
            chemins.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z")
    return " ".join(chemins)


def monde(assets, tuiles, contours):
    """La carte (vue d'ensemble + tuiles détaillées + contours de communes), dans un repère transformable."""
    shutil.copy(CARTE / "creuse.png", assets / "creuse.png")
    h = ['        <div id="monde" style="position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0">',
         '<img src="assets/creuse.png" style="position:absolute;left:0;top:0;width:1080px;height:1920px"/>']
    for i in tuiles:
        shutil.copy(CARTE / f"zoom_{i + 1}.png", assets / f"zoom_{i + 1}.png")
        gx, gy, gw, gh = boite_zoom(i)[1]
        h.append(f'<img id="tuile{i}" src="assets/zoom_{i + 1}.png" style="position:absolute;left:{gx:.3f}px;top:{gy:.3f}px;'
                 f'width:{gw:.3f}px;height:{gh:.3f}px;opacity:0"/>')
    h.append('<svg width="1080" height="1920" style="position:absolute;left:0;top:0;overflow:visible">')
    for i in contours:
        h.append(f'<path id="com{i}" d="{contour_commune(GISEMENTS[i][2])}" fill="rgba(242,181,68,0.08)" stroke="#f2b544" '
                 f'stroke-width="{4.5 / ZOOM:.3f}" stroke-linejoin="round" opacity="0"/>')  # visible seulement une fois zoomé
    h.append('</svg></div>')
    return "".join(h)


def ecr(p, vue):
    tx, ty, s = vue
    return p[0] * s + tx, p[1] * s + ty


def precedent(k):
    """Gisement de la séquence carte précédente (celui d'où l'on dézoome)."""
    avant = [i for i in range(min(k, len(GISEMENTS))) if GISEMENTS[i][6]]
    return avant[-1] if avant else None


def carte(k, duree, assets, fin=False):
    """Séquence carte du gisement k (ou fin : dézoom sur les dix gisements avec leurs photos)."""
    prec = precedent(k)
    ensemble = (0.0, 0.0, 1.0)
    depart = vue_zoom(prec) if prec is not None else ensemble
    zoom = vue_zoom(k) if not fin else None
    preparer_fond(CARTE / "creuse.png", assets)
    tuiles = [i for i in (prec, None if fin else k) if i is not None]
    corps = [monde(assets, tuiles, tuiles),
             '        <div style="position:absolute;left:0;top:0;width:1080px;height:520px;background:linear-gradient(180deg,rgba(0,0,0,0.7),rgba(0,0,0,0))"></div>']
    script = [f'      gsap.set("#monde", {{ x: {depart[0]:.2f}, y: {depart[1]:.2f}, scale: {depart[2]} }});']
    # temps forts
    t_dez = 0.1
    d_dez = 1.3 if prec is not None else 0.0
    t_pop = (t_dez + d_dez + 0.15) if prec is not None else 0.4
    t_zoom = t_pop + 0.55
    d_zoom = 1.4
    if prec is not None:
        script += [f'      tl.set("#tuile{prec}", {{ opacity: 1 }}, 0); tl.set("#com{prec}", {{ opacity: 1 }}, 0);',
                   f'      tl.to("#tuile{prec}", {{ opacity: 0, duration: 0.5 }}, {t_dez:.2f});',
                   f'      tl.to("#com{prec}", {{ opacity: 0, duration: 0.4 }}, {t_dez:.2f});',
                   f'      tl.to("#monde", {{ x: 0, y: 0, scale: 1, duration: {d_dez}, ease: "power2.inOut" }}, {t_dez:.2f});']
    if not fin:
        script.append(f'      tl.to("#monde", {{ x: {zoom[0]:.2f}, y: {zoom[1]:.2f}, scale: {zoom[2]}, duration: {d_zoom}, ease: "power2.inOut" }}, {t_zoom:.2f});')

    # repères (villes), visibles en vue d'ensemble seulement, effacés dès qu'un gisement s'affiche
    if not fin:
        for j, (nom, la, lo) in enumerate(VILLES):
            x, y = ecran(la, lo)
            corps.append(f'        <div id="ville{j}" style="position:absolute;left:{x - 5:.1f}px;top:{y - 17:.1f}px;display:flex;align-items:center;gap:8px;opacity:0">'
                         '<span style="width:10px;height:10px;border-radius:2px;background:#e8e2f0"></span>'
                         f'<span style="font-size:24px;font-weight:600;color:#e8e2f0;white-space:nowrap;text-shadow:0 2px 6px #000">{nom}</span></div>')
            t_in = (t_dez + d_dez - 0.5) if prec is not None else 0.0
            script.append(f'      tl.fromTo("#ville{j}", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.35 }}, {max(t_in, 0):.2f});')
            script.append(f'      tl.to("#ville{j}", {{ opacity: 0, duration: 0.25 }}, {t_pop - 0.05:.2f});')

    # points des gisements : déjà vus (petits) et courant (gros, avec halo) ; positions écran suivant la carte
    n = len(GISEMENTS) if fin else k + 1
    for i in range(n):
        p = ecran(*GISEMENTS[i][3:5])
        a, b = ecr(p, depart), p
        courant = (i == k and not fin)
        r = 15 if courant else 9
        corps.append(f'        <div id="pt{i}" style="position:absolute;left:{-r}px;top:{-r}px;width:{2 * r}px;height:{2 * r}px;border-radius:50%;'
                     f'background:#f2b544;border:{4 if courant else 3}px solid #fff;box-shadow:0 0 {22 if courant else 10}px rgba(242,181,68,0.9)"></div>')
        script.append(f'      gsap.set("#pt{i}", {{ x: {a[0]:.1f}, y: {a[1]:.1f} }});')
        if prec is not None:
            script.append(f'      tl.to("#pt{i}", {{ x: {b[0]:.1f}, y: {b[1]:.1f}, duration: {d_dez}, ease: "power2.inOut" }}, {t_dez:.2f});')
        if courant:
            c = ecr(p, zoom)
            script += [f'      tl.fromTo("#pt{i}", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(3)" }}, {t_pop:.2f});',
                       f'      tl.to("#pt{i}", {{ x: {c[0]:.1f}, y: {c[1]:.1f}, duration: {d_zoom}, ease: "power2.inOut" }}, {t_zoom:.2f});']
        elif not fin:
            # les autres points suivent la carte pendant le zoom (et sortent du cadre)
            c = ecr(p, zoom)
            script.append(f'      tl.to("#pt{i}", {{ x: {c[0]:.1f}, y: {c[1]:.1f}, duration: {d_zoom}, ease: "power2.inOut" }}, {t_zoom:.2f});')

    if fin:
        return carte_finale(duree, assets, corps, script, t_dez + d_dez)

    nom, sous, code, la, lo, ph, _ = GISEMENTS[k]
    # étiquette du point en vue d'ensemble
    px_, py_ = ecran(la, lo)
    cote = "g" if px_ > 620 else "d"
    corps.append(f'        <div id="nom-ensemble" style="position:absolute;top:{py_ - 26:.0f}px;'
                 + (f'right:{1080 - px_ + 26:.0f}px;' if cote == "g" else f'left:{px_ + 26:.0f}px;')
                 + 'padding:6px 18px;border-radius:24px;background:rgba(0,0,0,0.75);border:2px solid #f2b544;'
                 f'font-size:32px;font-weight:800;white-space:nowrap">{nom}</div>')
    script += [f'      tl.fromTo("#nom-ensemble", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {t_pop + 0.1:.2f});',
               f'      tl.to("#nom-ensemble", {{ opacity: 0, duration: 0.3 }}, {t_zoom + 0.1:.2f});']
    # vue zoomée : tuile détaillée, contour de la commune, titre, sous-titre, photo
    t_arr = t_zoom + d_zoom
    script += [f'      tl.to("#tuile{k}", {{ opacity: 1, duration: 0.5 }}, {t_arr - 0.35:.2f});',
               f'      tl.to("#com{k}", {{ opacity: 1, duration: 0.6 }}, {t_arr - 0.2:.2f});']
    corps.append(tete("Creuse (23)", nom))
    script.append(entree("#tete", t_zoom + 0.7))
    if sous:
        corps.append(f'        <div id="sous" style="position:absolute;left:0;width:1080px;top:{CIBLE[1] + 34}px;text-align:center">'
                     '<span style="padding:6px 18px;border-radius:22px;background:rgba(0,0,0,0.72);font-size:28px;font-weight:700">'
                     f'{sous}</span></div>')
        script.append(apparition("#sous", t_arr - 0.1, 10, 0.4))
    if k in CARTES_POSTALES:
        # cartes postales anciennes, en bas, légèrement inclinées
        for j, (f, (x, y, rot)) in enumerate(zip(CARTES_POSTALES[k], [(110, 760, -3), (520, 790, 3)])):
            shutil.copy(ARCH / f, assets / f)
            corps.append(f'        <div id="cp{j}" class="archive" style="left:{x}px;top:{y}px;width:450px;height:292px;transform:rotate({rot}deg)">'
                         f'<img src="assets/{f}"/></div>')
            script.append(f'      tl.fromTo("#cp{j}", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {t_arr + 0.1 + 0.35 * j:.2f});')
        corps.append('        <div id="cp-leg" class="petit" style="position:absolute;left:110px;top:1080px;width:860px;text-align:center;font-size:26px">'
                     'Cartes postales anciennes</div>')
        script.append(apparition("#cp-leg", t_arr + 0.6, 10, 0.4))
    else:
        # photo de la collection, reliée au point
        shutil.copy(SRC / ph, assets / ph)
        cx, cy = (850, 900) if ecr(ecran(la, lo), zoom)[0] < 600 and k % 2 == 0 else (230, 900)
        corps.append(f'        <svg width="1080" height="1920" style="position:absolute;left:0;top:0"><line id="trait" x1="{CIBLE[0]}" y1="{CIBLE[1]}" '
                     f'x2="{cx}" y2="{cy}" stroke="rgba(255,255,255,0.85)" stroke-width="3"/></svg>')
        corps.append(f'        <div id="vignette" style="position:absolute;left:{cx - 115}px;top:{cy - 115}px;width:230px;height:230px;border-radius:50%;'
                     f'overflow:hidden;border:6px solid #f2b544;box-shadow:0 12px 36px rgba(0,0,0,0.75)">'
                     f'<img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>')
        script += [f'      tl.fromTo("#trait", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t_arr + 0.1:.2f});',
                   f'      tl.fromTo("#vignette", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.8)" }}, {t_arr + 0.15:.2f});']
    return page(duree, "\n".join(corps), "#photo img { filter:none; } #photo-voile { display:none; }", "\n".join(script), zoom_fond=False)


# emplacement des vignettes de la carte finale : colonne gauche / droite, triées du nord au sud
NOMS_COURTS = {"Lavaveix-les-Mines": "Lavaveix", "Saint-Silvain-Bellegarde": "Saint-Silvain"}


def carte_finale(duree, assets, corps, script, t0):
    """Les dix gisements sur la carte de la Creuse, chacun avec sa photo."""
    pts = {i: ecran(*GISEMENTS[i][3:5]) for i in range(len(GISEMENTS))}
    gauche = sorted([0, 1, 3, 9, 8], key=lambda i: pts[i][1])
    droite = sorted([2, 5, 4, 6, 7], key=lambda i: pts[i][1])
    ys = (470, 625, 780, 935, 1090)
    fentes = {i: (175, y) for i, y in zip(gauche, ys)}
    fentes.update({i: (905, y) for i, y in zip(droite, ys)})
    lignes = []
    for rang, i in enumerate(sorted(fentes, key=lambda i: (fentes[i][1], fentes[i][0]))):
        nom, *_r, ph, _c = GISEMENTS[i]
        shutil.copy(SRC / ph, assets / ph)
        fx, fy = fentes[i]
        px_, py_ = pts[i]
        t = t0 + 0.2 + 0.22 * rang
        lignes.append(f'<line id="l{i}" x1="{px_:.1f}" y1="{py_:.1f}" x2="{fx}" y2="{fy}" stroke="rgba(255,255,255,0.8)" stroke-width="2.5" opacity="0"/>')
        corps.append(f'        <div id="v{i}" style="position:absolute;left:{fx - 85}px;top:{fy - 58}px;width:170px;text-align:center">'
                     '<div style="width:110px;height:110px;margin:0 auto;border-radius:50%;overflow:hidden;border:4px solid #f2b544;'
                     f'box-shadow:0 10px 30px rgba(0,0,0,0.75)"><img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>'
                     '<div style="display:inline-block;margin-top:4px;padding:2px 10px;border-radius:12px;background:rgba(0,0,0,0.72);'
                     f'font-size:20px;font-weight:800;white-space:nowrap">{NOMS_COURTS.get(nom, nom)}</div></div>')
        script += [f'      tl.to("#l{i}", {{ opacity: 1, duration: 0.3 }}, {t:.2f});',
                   f'      tl.fromTo("#v{i}", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {t + 0.05:.2f});']
    corps.insert(2, '        <svg width="1080" height="1920" style="position:absolute;left:0;top:0">' + "".join(lignes) + '</svg>')
    corps.append(tete("Ma collection", "Minéraux de la Creuse"))
    script.append(entree("#tete", t0))
    return page(duree, "\n".join(corps), "#photo img { filter:none; } #photo-voile { display:none; }", "\n".join(script), zoom_fond=False)


# ---------------------------------------------------------------- archives (cartes postales) et compteurs

# (cartes postales, légende, [(mots déclencheurs, [morceaux], légende du chiffre)]) ; morceau : texte ou (départ, arrivée)
ARCHIVES = {
    "montebras": (["A1.jpg", "A3.jpg", "A5.jpg"], "Mines de Montebras, cartes postales anciennes",
                  [("De 1868 à 1914", [(1800, 1868), " – ", (1800, 1914)], "exploitation des mines"),
                   ("livrent environ 300", ["≈ ", (0, 300), " t"], "d'étain")]),
    "lavaveix": (["L1.jpg", "L8.jpg", "L3.jpg", "L2.jpg"], "Lavaveix-les-Mines, cartes postales anciennes",
                 [("Concédé en 1817", [(1750, 1817), " – ", (1900, 1969)], "concession, fin des travaux"),
                  ("à 354 000 tonnes", [(0, 354000), " t"], "de charbon en 1874"),
                  ("emploie 2 000 ouvriers", [(0, 2000)], "ouvriers en 1876")]),
}


def archives(nom, duree, instants, assets):
    images, legende, blocs = ARCHIVES[nom]
    preparer_fond(ARCH / images[0], assets, flou=True)
    corps, script = [], []
    n = len(images)
    pas = duree / n
    for j, f in enumerate(images):
        shutil.copy(ARCH / f, assets / f)
        corps.append(f'        <div id="a{j}" class="archive" style="left:110px;top:250px;width:860px;height:600px;opacity:0"><img src="assets/{f}"/></div>')
        t = j * pas
        script.append(f'      tl.fromTo("#a{j}", {{ opacity: 0, scale: 0.97 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "power2.out" }}, {max(t, 0.05):.2f});')
        script.append(f'      tl.fromTo("#a{j} img", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {pas + 0.5:.2f}, ease: "none" }}, {t:.2f});')
        if j < n - 1:
            script.append(f'      tl.to("#a{j}", {{ opacity: 0, duration: 0.45 }}, {t + pas:.2f});')
    corps.append(f'        <div id="leg" class="petit" style="position:absolute;left:110px;top:870px;width:860px;text-align:center;font-size:26px">{legende}</div>')
    script.append(apparition("#leg", 0.4, 10, 0.4))
    cases = []
    for j, (mots, morceaux, leg) in enumerate(blocs):
        t = min(max(instants[j] - 0.6, 0.3), duree - 1.6)  # le compteur tourne pendant la lecture
        spans = []
        script.append(apparition(f"#chiffre{j}", t, 16, 0.45))
        for m, mor in enumerate(morceaux):
            if isinstance(mor, tuple):
                sid = f"n{j}_{m}"
                sep = mor[1] >= 1000 and not (1700 <= mor[1] <= 2100 and mor[0] >= 1700)  # pas d'espace dans les années
                spans.append(f'<span id="{sid}">{fmt(mor[0]) if sep else mor[0]}</span>')
                script.append(compteur(f"#{sid}", mor[0], mor[1], t + 0.1, 1.3, separateur=sep))
            else:
                spans.append(mor)
        taille = 50 if len(blocs) == 2 else 40
        cases.append(f'<div id="chiffre{j}" style="flex:auto;text-align:center;padding:14px 10px;border-radius:22px;background:rgba(255,255,255,0.06)">'
                     f'<div class="grand" style="font-size:{taille}px">{"".join(spans)}</div>'
                     f'<div class="petit" style="margin-top:8px;font-size:23px">{leg}</div></div>')
    corps.append('        <div id="chiffres" class="panneau" style="position:absolute;left:110px;top:940px;width:860px;padding:16px;'
                 'display:flex;gap:14px">' + "".join(cases) + '</div>')
    script.append(f'      tl.fromTo("#chiffres", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {min(max(instants[0] - 0.7, 0.2), duree - 1.7):.2f});')
    return page(duree, "\n".join(corps), "", "\n".join(script))


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
        if nom in CARTES:
            html = carte(CARTES[nom], d, assets)
        elif nom == "carte_fin":
            html = carte(len(GISEMENTS), d, assets, fin=True)
        elif nom in ARCHIVES:
            html = archives(nom, d, [rel(nom, m) for m, _, _ in ARCHIVES[nom][2]], assets)
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
