"""Séquences HyperFrames de « Fluorites de France ».

Fil conducteur : carte de France en relief (IGN, voir carte_fond.py). Pour chaque gisement, la carte dézoome depuis le
gisement précédent, le point apparaît, la carte zoome dessus, puis les chiffres clés s'affichent avec des compteurs.
Toujours une image en fond (carte, photo du minéral), jamais de fond violet.

python3 projets/fluorites/hyperframes_scenes.py               -> compose et rend tout
python3 projets/fluorites/hyperframes_scenes.py carte_1       -> une seule séquence
python3 projets/fluorites/hyperframes_scenes.py --check       -> compose et vérifie sans rendre

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
.unite { font-size:46px; font-weight:700; text-shadow:0 3px 14px rgba(0,0,0,0.8); }
.petit { font-size:30px; font-weight:600; color:var(--gris); text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.badge { display:inline-block; padding:12px 26px; border-radius:40px; font-size:32px; font-weight:700;
  background:rgba(0,0,0,0.6); border:2px solid rgba(199,125,255,0.75); }
.panneau { background:rgba(8,6,12,0.7); border:2px solid rgba(199,125,255,0.55); border-radius:34px;
  box-shadow:0 24px 60px rgba(0,0,0,0.55); }
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


def compteur(sel, depart, arrivee, t, d, decimales=0, separateur=False, prefixe="", suffixe=""):
    """Compteur animé, au format français (virgule décimale, espace fine pour les milliers)."""
    var = "c_" + sel.strip("#").replace("-", "_")
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


def fmt(v):
    return f"{v:,}".replace(",", " ")


# ---------------------------------------------------------------- carte de France : dézoom, point, zoom, chiffres

# Chiffres clés de chaque gisement : (mots du texte qui les déclenchent, [morceaux], légende).
# Un morceau est un texte fixe ou un compteur (départ, arrivée).
CHIFFRES = {
    0: [("70 000 à 100 000", [(0, 70000), " – ", (0, 100000), " t"], "de spath métallurgique"),
        ("de 1925 à 1947", [(1890, 1925), " – ", (1890, 1947)], "exploitation")],
    1: [("un filon de", [(0, 25), " cm – 1 m"], "épaisseur du filon"),
        ("en 1924-1926", [(1890, 1924), "-26 · ", (1940, 1968), "-76"], "deux brèves exploitations")],
    2: [("fut exploité", [(1890, 1920), " – ", (1890, 1977)], "exploitation"),
        ("Il a livré", [(0, 386000), " t"], "de produits marchands"),
        ("d'un minerai titrant", [(0, 95), " %"], "de CaF₂, au mieux")],
    4: [("plus de 700 000", ["+ de ", (0, 700000), " t"], "de minerai pour le district")],
    6: [("découvert en 1926", [(1890, 1926), " – ", (1890, 1974)], "exploitation"),
        ("Moins de 10 000", ["< ", (0, 10000), " t"], "de spath métallurgique")],
    7: [("Exploité dès 1959", [(1920, 1959)], "début de l'exploitation"),
        ("c'est le plus gros", [(0, 150000), " – ", (0, 200000), " t"], "de minerai brut")],
}

# déclencheur du premier mot de chaque séquence carte (nom de la séquence -> index du gisement)
CARTES = {f"carte_{i + 1}": i for i in range(len(GISEMENTS))}


def contour_departement(code, tol=1.2):
    """Contour du département en coordonnées de la vue de France (tracé simplifié, tolérance en px de zoom)."""
    d = json.loads((CARTE / "departements.geojson").read_text())
    f = next(f for f in d["features"] if f["properties"]["code_insee"] == code)
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    chemins = []
    pas = tol / 9.0  # tol px à l'échelle du zoom
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
    """La carte (vue de France + tuiles détaillées + contours de départements), dans un repère transformable."""
    shutil.copy(CARTE / "france.png", assets / "france.png")
    h = ['        <div id="monde" style="position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0">',
         '<img src="assets/france.png" style="position:absolute;left:0;top:0;width:1080px;height:1920px"/>']
    for i in tuiles:
        shutil.copy(CARTE / f"zoom_{i + 1}.png", assets / f"zoom_{i + 1}.png")
        gx, gy, gw, gh = boite_zoom(i)[1]
        h.append(f'<img id="tuile{i}" src="assets/zoom_{i + 1}.png" style="position:absolute;left:{gx:.3f}px;top:{gy:.3f}px;'
                 f'width:{gw:.3f}px;height:{gh:.3f}px;opacity:0"/>')
    h.append('<svg width="1080" height="1920" style="position:absolute;left:0;top:0;overflow:visible">')
    for i in contours:
        h.append(f'<path id="dep{i}" d="{contour_departement(GISEMENTS[i][3])}" fill="rgba(242,181,68,0.06)" stroke="#f2b544" '
                 f'stroke-width="{4.5 / ZOOM:.3f}" stroke-linejoin="round" opacity="0"/>')  # visible seulement une fois zoomé
    h.append('</svg></div>')
    return "".join(h)


def ecr(p, vue):
    tx, ty, s = vue
    return p[0] * s + tx, p[1] * s + ty


def carte(k, duree, instants, assets, fin=False):
    """Séquence carte du gisement k (ou fin : dézoom sur les huit gisements avec leurs photos)."""
    prec = k - 1 if k > 0 else None
    france = (0.0, 0.0, 1.0)
    depart = vue_zoom(prec) if prec is not None else france
    zoom = vue_zoom(k) if not fin else None
    preparer_fond(CARTE / "france.png", assets)
    tuiles = [i for i in (prec, None if fin else k) if i is not None]
    contours = tuiles
    corps = [monde(assets, tuiles, contours),
             '        <div style="position:absolute;left:0;top:0;width:1080px;height:520px;background:linear-gradient(180deg,rgba(0,0,0,0.7),rgba(0,0,0,0))"></div>']
    script = [f'      gsap.set("#monde", {{ x: {depart[0]:.2f}, y: {depart[1]:.2f}, scale: {depart[2]} }});']
    # temps forts
    t_dez = 0.1
    d_dez = 1.3 if prec is not None else 0.0
    t_pop = (t_dez + d_dez + 0.15) if prec is not None else 0.45
    t_zoom = t_pop + 0.65
    d_zoom = 1.5
    if prec is not None:
        script += [f'      tl.set("#tuile{prec}", {{ opacity: 1 }}, 0); tl.set("#dep{prec}", {{ opacity: 1 }}, 0);',
                   f'      tl.to("#tuile{prec}", {{ opacity: 0, duration: 0.5 }}, {t_dez:.2f});',
                   f'      tl.to("#dep{prec}", {{ opacity: 0, duration: 0.4 }}, {t_dez:.2f});',
                   f'      tl.to("#monde", {{ x: 0, y: 0, scale: 1, duration: {d_dez}, ease: "power2.inOut" }}, {t_dez:.2f});']
    if not fin:
        script.append(f'      tl.to("#monde", {{ x: {zoom[0]:.2f}, y: {zoom[1]:.2f}, scale: {zoom[2]}, duration: {d_zoom}, ease: "power2.inOut" }}, {t_zoom:.2f});')

    # repères (villes), visibles en vue de France seulement, effacés dès qu'un gisement s'affiche
    if not fin:
        for j, (nom, la, lo) in enumerate(VILLES):
            x, y = ecran(la, lo)
            corps.append(f'        <div id="ville{j}" style="position:absolute;left:{x - 5:.1f}px;top:{y - 17:.1f}px;display:flex;align-items:center;gap:8px;opacity:0">'
                         '<span style="width:10px;height:10px;border-radius:50%;background:#e8e2f0"></span>'
                         f'<span style="font-size:24px;font-weight:600;color:#e8e2f0;white-space:nowrap;text-shadow:0 2px 6px #000">{nom}</span></div>')
            t_in = (t_dez + d_dez - 0.5) if prec is not None else 0.0
            script.append(f'      tl.fromTo("#ville{j}", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.35 }}, {max(t_in, 0):.2f});')
            script.append(f'      tl.to("#ville{j}", {{ opacity: 0, duration: 0.25 }}, {t_pop - 0.05:.2f});')

    # points des gisements : déjà vus (petits) et courant (gros, avec halo) ; positions écran suivant la carte
    n = len(GISEMENTS) if fin else k + 1
    for i in range(n):
        p = ecran(*GISEMENTS[i][4:6])
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
            # les autres points sortent du cadre pendant le zoom : on les éteint
            script.append(f'      tl.to("#pt{i}", {{ opacity: 0, duration: 0.4 }}, {t_zoom:.2f});')

    if fin:
        return carte_finale(duree, assets, corps, script, t_dez + d_dez)

    nom, commune, dep, code, la, lo, ph = GISEMENTS[k]
    shutil.copy(SRC / ph, assets / ph)
    # étiquette du point en vue de France
    px_, py_ = ecran(la, lo)
    cote = "g" if px_ > 640 else "d"
    corps.append(f'        <div id="nom-france" style="position:absolute;top:{py_ - 26:.0f}px;'
                 + (f'right:{1080 - px_ + 26:.0f}px;' if cote == "g" else f'left:{px_ + 26:.0f}px;')
                 + 'padding:6px 18px;border-radius:24px;background:rgba(0,0,0,0.75);border:2px solid #f2b544;'
                 f'font-size:32px;font-weight:800;white-space:nowrap">{nom}</div>')
    script += [f'      tl.fromTo("#nom-france", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {t_pop + 0.1:.2f});',
               f'      tl.to("#nom-france", {{ opacity: 0, duration: 0.3 }}, {t_zoom + 0.1:.2f});']
    # vue zoomée : tuile détaillée, contour du département, titre, commune, photo
    t_arr = t_zoom + d_zoom
    script += [f'      tl.to("#tuile{k}", {{ opacity: 1, duration: 0.5 }}, {t_arr - 0.35:.2f});',
               f'      tl.to("#dep{k}", {{ opacity: 1, duration: 0.6 }}, {t_arr - 0.2:.2f});']
    corps.append(tete(f"{dep} ({code})", nom))
    script.append(entree("#tete", t_zoom + 0.8))
    if commune:
        corps.append(f'        <div id="commune" style="position:absolute;left:0;width:1080px;top:{CIBLE[1] + 34}px;text-align:center">'
                     '<span style="padding:6px 18px;border-radius:22px;background:rgba(0,0,0,0.72);font-size:28px;font-weight:700">'
                     f'{commune}</span></div>')
        script.append(apparition("#commune", t_arr - 0.1, 10, 0.4))
    # photo de la collection, reliée au point
    cx, cy = (820, 640) if k % 2 == 0 else (260, 640)
    corps.append(f'        <svg width="1080" height="1920" style="position:absolute;left:0;top:0"><line id="trait" x1="{CIBLE[0]}" y1="{CIBLE[1]}" '
                 f'x2="{cx}" y2="{cy}" stroke="rgba(255,255,255,0.85)" stroke-width="3"/></svg>')
    corps.append(f'        <div id="vignette" style="position:absolute;left:{cx - 115}px;top:{cy - 115}px;width:230px;height:230px;border-radius:50%;'
                 f'overflow:hidden;border:6px solid #f2b544;box-shadow:0 12px 36px rgba(0,0,0,0.75)">'
                 f'<img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>')
    script += [f'      tl.fromTo("#trait", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t_arr + 0.1:.2f});',
               f'      tl.fromTo("#vignette", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.8)" }}, {t_arr + 0.15:.2f});']
    # chiffres clés
    blocs = CHIFFRES.get(k, [])
    if blocs:
        cases = []
        for j, (mots, morceaux, legende) in enumerate(blocs):
            spans = []
            t = max(instants[j] if j < len(instants) else 0, t_arr + 0.3 + 0.5 * j)
            t = min(t, duree - 1.6)
            script.append(apparition(f"#chiffre{j}", t, 16, 0.45))
            for m, mor in enumerate(morceaux):
                if isinstance(mor, tuple):
                    sid = f"n{j}_{m}"
                    spans.append(f'<span id="{sid}">{fmt(mor[0]) if mor[1] >= 10000 else mor[0]}</span>')
                    script.append(compteur(f"#{sid}", mor[0], mor[1], t + 0.1, 1.3, separateur=mor[1] >= 10000))
                else:
                    spans.append(mor)
            taille = 64 if len(blocs) == 1 else (54 if len(blocs) == 2 else 46)
            cases.append(f'<div id="chiffre{j}" style="flex:auto;text-align:center;padding:16px 12px;border-radius:24px;background:rgba(255,255,255,0.06)">'
                         f'<div class="grand" style="font-size:{taille}px">{"".join(spans)}</div>'
                         f'<div class="petit" style="margin-top:8px;font-size:26px">{legende}</div></div>')
        corps.append('        <div id="chiffres" class="panneau" style="position:absolute;left:110px;top:900px;width:860px;padding:18px;'
                     'display:flex;gap:16px">' + "".join(cases) + '</div>')
        script.append(f'      tl.fromTo("#chiffres", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, '
                      f'{min(max(instants[0] if instants else 0, t_arr + 0.3), duree - 1.6) - 0.1:.2f});')
    return page(duree, "\n".join(corps), "#photo img { filter:none; } #photo-voile { display:none; }", "\n".join(script), zoom_fond=False)


def carte_finale(duree, assets, corps, script, t0):
    """Les huit gisements sur la carte de France, chacun avec sa photo."""
    fentes = {}
    pts = {i: ecran(*GISEMENTS[i][4:6]) for i in range(len(GISEMENTS))}
    for i, y in zip(sorted([0, 1, 2, 6], key=lambda i: pts[i][1]), (560, 745, 930, 1100)):
        fentes[i] = (180, y)
    fentes[3] = (420, 430)
    for i, y in zip(sorted([4, 5, 7], key=lambda i: pts[i][1]), (430, 790, 990)):
        fentes[i] = (900, y)
    lignes = []
    for i, (nom, *_r, ph) in enumerate(GISEMENTS):
        shutil.copy(SRC / ph, assets / ph)
        fx, fy = fentes[i]
        px_, py_ = pts[i]
        t = t0 + 0.2 + 0.28 * i
        lignes.append(f'<line id="l{i}" x1="{px_:.1f}" y1="{py_:.1f}" x2="{fx}" y2="{fy}" stroke="rgba(255,255,255,0.8)" stroke-width="2.5" opacity="0"/>')
        corps.append(f'        <div id="v{i}" style="position:absolute;left:{fx - 110}px;top:{fy - 68}px;width:220px;text-align:center">'
                     '<div style="width:136px;height:136px;margin:0 auto;border-radius:50%;overflow:hidden;border:5px solid #f2b544;'
                     f'box-shadow:0 10px 30px rgba(0,0,0,0.75)"><img src="assets/{ph}" style="width:100%;height:100%;object-fit:cover"/></div>'
                     '<div style="display:inline-block;margin-top:6px;padding:2px 12px;border-radius:14px;background:rgba(0,0,0,0.72);'
                     f'font-size:24px;font-weight:800;white-space:nowrap">{nom}</div></div>')
        script += [f'      tl.to("#l{i}", {{ opacity: 1, duration: 0.3 }}, {t:.2f});',
                   f'      tl.fromTo("#v{i}", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {t + 0.05:.2f});']
    corps.insert(2, '        <svg width="1080" height="1920" style="position:absolute;left:0;top:0">' + "".join(lignes) + '</svg>')
    corps.append(tete("Collection jeremineralogie", "Fluorites de France"))
    script.append(entree("#tete", t0))
    return page(duree, "\n".join(corps), "#photo img { filter:none; } #photo-voile { display:none; }", "\n".join(script), zoom_fond=False)


# ---------------------------------------------------------------- fiche de la fluorite (photo du minéral en fond)

CSS_FICHE = """
#carte { position:absolute; top:450px; left:110px; width:860px; padding:34px 30px 30px; }
#formule { text-align:center; font-weight:800; font-size:110px; white-space:nowrap; }
#formule sub { font-size:0.55em; vertical-align:-0.25em; }
#nom-chimique { margin-top:8px; text-align:center; font-size:34px; font-weight:600; color:var(--or); }
#elements { margin-top:24px; display:flex; justify-content:center; gap:40px; }
.el { width:170px; text-align:center; }
.rond { width:100px; height:100px; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:44px; font-weight:800; background:var(--violet); box-shadow:0 0 24px rgba(123,44,191,0.6); }
.rond.f { background:#123a2a; border:3px solid #7fe0b0; color:#9ff0c6; box-shadow:0 0 26px rgba(127,224,176,0.5); }
.el-nom { margin-top:10px; font-size:27px; font-weight:600; color:var(--gris); }
#tuiles { position:absolute; top:880px; left:110px; width:860px; display:flex; gap:18px; }
.tuile { flex:1; text-align:center; padding:20px 10px; }
.tuile .grand { font-size:72px; }
.tuile .petit { margin-top:8px; font-size:26px; }
"""


def fiche_fluorite(duree, instants, assets):
    t_mohs, t_nom, t_fondant = instants
    preparer_fond(SRC / "photo_19.jpg", assets)
    corps = "\n".join([
        tete("Composition", "La fluorite"),
        '        <div id="carte" class="panneau"><div id="formule">CaF<sub>2</sub></div>'
        '<div id="nom-chimique">Fluorure de calcium</div>'
        '<div id="elements"><div class="el"><div class="rond">Ca</div><div class="el-nom">calcium</div></div>'
        '<div class="el"><div class="rond f">F</div><div class="el-nom">fluor ×2</div></div></div></div>',
        '        <div id="tuiles">'
        '<div class="tuile panneau" id="t-mohs"><div id="mohs" class="grand">0</div><div class="petit">dureté, étalon de Mohs</div></div>'
        '<div class="tuile panneau" id="t-nom"><div class="grand" style="font-size:58px;font-style:italic">fluere</div><div class="petit">« couler », en latin</div></div>'
        '<div class="tuile panneau" id="t-fondant"><div class="grand" style="font-size:52px">fondant</div><div class="petit">en métallurgie</div></div>'
        '</div>',
    ])
    script = [entree("#tete", 0.15),
              '      tl.fromTo("#carte", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.25);',
              '      tl.fromTo("#formule", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.8, ease: "power2.inOut" }, 0.4);',
              apparition("#nom-chimique", 0.9, 12, 0.35),
              '      tl.fromTo("#elements .el:nth-child(1)", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, 1.1);',
              '      tl.fromTo("#elements .el:nth-child(2)", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, 1.25);',
              apparition("#t-mohs", t_mohs, 16, 0.45), compteur("#mohs", 0, 4, t_mohs + 0.1, 1.2),
              apparition("#t-nom", t_nom, 16, 0.45),
              apparition("#t-fondant", t_fondant, 16, 0.45)]
    return page(duree, corps, CSS_FICHE, "\n".join(script))


def production(duree, t_tonnes, assets):
    preparer_fond(SRC / "photo_04.jpg", assets)
    corps = "\n".join([
        tete("Production française", "Depuis 1861"),
        '        <div id="bloc" style="position:absolute;top:560px;width:100%;text-align:center">'
        '<div id="tonnes" class="grand" style="font-size:230px">0</div>'
        '<div class="unite">millions de tonnes</div>'
        '<div class="petit" style="margin-top:14px">extraites en France (estimation BRGM, 1999)</div></div>',
        '        <div id="annee-bloc" style="position:absolute;top:470px;width:100%;text-align:center"><span id="annee" class="badge">1800</span></div>',
    ])
    script = [entree("#tete", 0.15), apparition("#annee-bloc", 0.3, 12, 0.4), compteur("#annee", 1800, 1861, 0.35, 1.0),
              apparition("#bloc", min(t_tonnes, duree - 2), 30), compteur("#tonnes", 0, 10.3, min(t_tonnes, duree - 2) + 0.1, 1.5, decimales=1)]
    return page(duree, corps, "#annee-bloc .badge { font-size:40px; }", "\n".join(script))


def calas_1971(duree, t_badge, assets):
    preparer_fond(SRC / "photo_07.jpg", assets)
    corps = "\n".join([
        tete("Valzergues", "Georges Calas"),
        '        <div id="annee" class="grand" style="position:absolute;top:560px;width:100%;text-align:center;font-size:250px">1940</div>',
        '        <div id="legende" class="petit" style="position:absolute;top:850px;left:110px;width:860px;text-align:center;font-size:34px">'
        'L\'origine des couleurs de la fluorite</div>',
        '        <div id="badge" style="position:absolute;top:960px;width:100%;text-align:center"><span class="badge">Une première, selon le BRGM</span></div>',
    ])
    script = [entree("#tete", 0.15), apparition("#annee", 0.3, 30), compteur("#annee", 1940, 1971, 0.4, 1.6),
              apparition("#legende", 1.5), apparition("#badge", min(max(t_badge, 2.2), duree - 1.4))]
    return page(duree, corps, "", "\n".join(script))


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
            k = CARTES[nom]
            html = carte(k, d, [rel(nom, m) for m, _, _ in CHIFFRES.get(k, [])], assets)
        elif nom == "carte_fin":
            html = carte(len(GISEMENTS), d, [], assets, fin=True)
        elif nom == "fiche_fluorite":
            html = fiche_fluorite(d, [rel(nom, "elle est l'étalon"), rel(nom, "Son nom"), rel(nom, "Elle servait")], assets)
        elif nom == "production":
            html = production(d, rel(nom, "plus de 10"), assets)
        elif nom == "calas_1971":
            html = calas_1971(d, rel(nom, "Une première"), assets)
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
