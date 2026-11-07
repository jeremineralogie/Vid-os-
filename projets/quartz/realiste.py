"""Habillage HyperFrames des rendus réalistes (Blender) de « Les couleurs du quartz ».

Les images viennent de blender/scenes.py (structure, centres colorés) et blender/cristaux.py (cristaux), dans
sources/rendus/<scène>.png, avec la position des repères à l'écran (sources/rendus/<scène>.json).
Chaque scène déroule ses étapes une par une : une seule légende à la fois, au moins 4 s chacune.
Mention « Modèle 3D » (structure) ou « Illustration 3D » (cristaux) sur chaque séquence.

python3 projets/quartz/realiste.py                 -> compose chaque séquence à sa durée nominale et fait des aperçus
python3 projets/quartz/realiste.py --rendre        -> rend aussi les vidéos (aperçus)
Au montage : composer(nom, durée du plan) puis rendre (voir scenes_video.py).
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
RENDUS = ICI / "sources" / "rendus"
APERCUS = ICI / "exports" / "apercus_3d"

CSS = """
:root { --violet-clair:#c77dff; --gris:#d6d0e0; --or:#f2b544; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#000; }
#root { position:relative; width:100%; height:100%; font-family:"Montserrat", sans-serif; color:#fff; }
.plan { position:absolute; inset:0; overflow:hidden; }
.plan img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
#voile { position:absolute; inset:0; pointer-events:none;
  background: linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.55) 16%, rgba(0,0,0,0) 27%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.7) 100%); }
.tete { position:absolute; top:250px; left:110px; width:860px; text-align:center; }
.surtitre { font-size:30px; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:var(--violet-clair); text-shadow:0 2px 10px #000; }
.titre { margin-top:14px; font-size:76px; font-weight:800; white-space:nowrap; text-shadow:0 4px 18px rgba(0,0,0,0.8); }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
.etiquette { position:absolute; padding:8px 18px; border-radius:22px; background:rgba(8,6,12,0.92); border:2px solid var(--or);
  font-size:28px; font-weight:800; white-space:nowrap; box-shadow:0 8px 24px rgba(0,0,0,0.6); }
.etiquette small { display:block; font-size:21px; font-weight:600; color:#ede9f2; }
.legende { position:absolute; left:110px; width:860px; text-align:center; font-size:30px; font-weight:700; line-height:1.35;
  padding:16px 22px; border-radius:24px; background:rgba(8,6,12,0.78); border:2px solid rgba(199,125,255,0.5); }
.mention { position:absolute; left:110px; top:1176px; width:860px; text-align:right; font-size:20px; font-weight:600; font-style:italic;
  color:#fff; text-shadow:0 2px 6px #000, 0 0 12px #000; }
"""


def page(duree, corps, script):
    return f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duree:.2f}" data-width="1080" data-height="1920">
      <div id="scene" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1">
{corps}
        <div id="voile"></div>
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{script}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def tete(surtitre, titre):
    return (f'        <div class="tete" id="tete" style="z-index:5"><div class="surtitre">{surtitre}</div>'
            f'<div class="titre">{titre}</div><div class="filet"></div></div>')


def montre(sel, t, d=0.45):
    return f'      tl.fromTo("{sel}", {{ opacity: 0 }}, {{ opacity: 1, duration: {d} }}, {t:.2f});'


def cache(sel, t, d=0.4):
    return f'      tl.to("{sel}", {{ opacity: 0, duration: {d} }}, {t:.2f});'


def etiquette(ident, point, texte, sous="", dx=0, dy=-120, cote="centre"):
    """Étiquette reliée par un trait au point (x, y) de l'image."""
    x, y = point
    ex, ey = x + dx, y + dy
    ancre = {"centre": "translate(-50%,-100%)", "bas": "translate(-50%,0)", "gauche": "translate(-100%,-50%)",
             "droite": "translate(0,-50%)"}[cote]
    trait = (f'<svg id="{ident}-t" width="1080" height="1920" style="position:absolute;left:0;top:0;z-index:4;opacity:0">'
             f'<line x1="{x}" y1="{y}" x2="{ex}" y2="{ey}" stroke="#f2b544" stroke-width="3"/>'
             f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="#f2b544" stroke-width="3"/></svg>')
    boite = (f'<div id="{ident}" class="etiquette" style="left:{ex}px;top:{ey}px;transform:{ancre};z-index:5;opacity:0">'
             f'{texte}{f"<small>{sous}</small>" if sous else ""}</div>')
    return "        " + trait + boite


def montre_etiquette(ident, t):
    return montre(f"#{ident}-t", t, 0.3) + "\n" + montre(f"#{ident}", t + 0.1, 0.35)


def cache_etiquette(ident, t):
    return cache(f"#{ident}-t", t) + "\n" + cache(f"#{ident}", t)


def copie(nom, assets):
    shutil.copy(RENDUS / f"{nom}.png", assets / f"{nom}.png")
    return json.loads((RENDUS / f"{nom}.json").read_text())


def onde(ident, a, b, couleur="#7fe0b0", larg=6):
    """Rayonnement ondulé (SVG) du point a au point b, à tracer avec trace()."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    long = math.hypot(dx, dy)
    n = max(1, int(long // 34))
    ang = math.degrees(math.atan2(dy, dx))
    vagues = "".join(" q 8.5 -14 17 0 q 8.5 14 17 0" for _ in range(n))
    return (f'<path id="{ident}" d="M 0 0{vagues}" fill="none" stroke="{couleur}" stroke-width="{larg}" stroke-linecap="round" '
            f'transform="translate({a[0]:.0f} {a[1]:.0f}) rotate({ang:.1f}) scale({long / (34 * n):.3f} 1)" '
            f'style="filter:drop-shadow(0 0 8px {couleur})"/>')


def rayon(ident, pts, couleur="#fffbe8", larg=10):
    """Faisceau lumineux rectiligne (polyligne SVG)."""
    d = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    return (f'<path id="{ident}" d="{d}" fill="none" stroke="{couleur}" stroke-width="{larg}" stroke-linecap="round" '
            f'stroke-linejoin="round" style="filter:drop-shadow(0 0 10px {couleur})"/>')


def trace(sel, t, d=1.6):
    return (f'      tl.fromTo("{sel}", {{ strokeDasharray: 4000, strokeDashoffset: 4000 }}, '
            f'{{ strokeDashoffset: 0, duration: {d}, ease: "power1.inOut" }}, {t:.2f});')


def calque(contenu):
    return f'        <svg width="1080" height="1920" style="position:absolute;left:0;top:0;z-index:4">{contenu}</svg>'


# ---------------------------------------------------------------- déroulé par étapes
# Une seule information à la fois : chaque étape a sa légende, qui remplace la précédente, et dure au moins 4 s.

def etapes(liste, duree, t0=0.0, haut=1000):
    """liste : [(durée nominale, légende ou None, fonction(t, d) -> lignes de script)].
    Les durées sont étirées si la séquence est plus longue que prévu. Renvoie (corps, script)."""
    nominal = sum(d for d, _, _ in liste)
    k = max(1.0, (duree - t0) / nominal)
    corps, script, t = [], [], t0
    for n, (d, legende, actions) in enumerate(liste):
        d *= k
        if legende:
            corps.append(f'        <div id="leg{n}" class="legende" style="top:{haut}px;z-index:5;opacity:0">{legende}</div>')
            script.append(f'      tl.fromTo("#leg{n}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, {t + 0.2:.2f});')
            if n < len(liste) - 1:
                script.append(cache(f"#leg{n}", t + d - 0.45, 0.4))
        if actions:
            script += actions(t, d)
        t += d
    return corps, script


def debut(duree, surtitre, titre, mention):
    """Lignes communes : titre, mention, lent zoom sur les plans."""
    return ([tete(surtitre, titre), f'        <div class="mention" id="mention" style="z-index:5">{mention}</div>'],
            [montre("#tete", 0.1, 0.6), montre("#mention", 0.6)])


MODELE = "Modèle 3D, d'après la structure du quartz α"
ILLU = "Illustration 3D"


def zoom_lent(sel, duree, a=1.0, b=1.06, t=0.0):
    return f'      tl.fromTo("{sel}", {{ scale: {a} }}, {{ scale: {b}, duration: {duree:.2f}, ease: "none" }}, {t:.2f});'


# ---------------------------------------------------------------- 1. structure : un tétraèdre, puis le réseau

def structure(duree, assets):
    p = copie("tetraedre", assets)
    copie("reseau", assets)
    c0, s0 = debut(duree, "La structure", "Le quartz, SiO₂", "Modèle 3D, d'après la structure cristallographique du quartz α")
    corps = ['        <div id="p1" class="plan"><img id="i1" src="assets/tetraedre.png"/></div>',
             '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/reseau.png"/></div>', *c0,
             etiquette("e-si", p["si"], "Si", "silicium", dx=-190, dy=-40, cote="gauche"),
             etiquette("e-o", p["o1"], "O", "oxygène", dx=150, dy=-60, cote="droite")]

    def reseau(t, d):
        return [cache_etiquette("e-si", t), cache_etiquette("e-o", t),
                f'      tl.to("#p2", {{ opacity: 1, duration: 1.4, ease: "power2.inOut" }}, {t:.2f});',
                f'      tl.fromTo("#i2", {{ scale: 1.0, rotation: -3 }}, {{ scale: 1.1, rotation: 3, duration: {duree - t:.2f}, ease: "none" }}, {t:.2f});']

    c, sc = etapes([
        (2.5, None, None),
        (4.0, "Au centre, un atome de <b>silicium</b>", lambda t, d: [montre_etiquette("e-si", t + 0.3)]),
        (4.0, "Autour de lui, quatre atomes d'<b>oxygène</b>", lambda t, d: [montre_etiquette("e-o", t + 0.3)]),
        (4.0, "Ensemble, ils forment un tétraèdre : SiO₄", None),
        (4.5, "Les tétraèdres s'assemblent :<br/>chaque oxygène est partagé entre deux", reseau),
        (4.0, "Ils dessinent des canaux hexagonaux", None),
    ], duree)
    script = [zoom_lent("#i1", duree, 1.1, 1.0)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 2. morion : la roche et ses éléments radioactifs

def irradiation(duree, assets):
    p = copie("morion_roche", assets)
    c0, s0 = debut(duree, "Quartz morion", "L'irradiation naturelle", ILLU)
    cr = p["cristal"]
    # sources sur la roche, à des positions fixes à l'écran (au-dessus de la zone des sous-titres)
    p.update(g1=(190, 1185), g2=(870, 1215), g3=(360, 1260), g4=(720, 1255))
    sources = [("g1", "U", "uranium"), ("g2", "Th", "thorium"), ("g3", "K", "potassium")]
    ondes = "".join(onde(f"o-{g}", p[g], cr) for g, _, _ in sources) + onde("o-g4", p["g4"], cr)
    corps = ['        <div class="plan"><img id="i1" src="assets/morion_roche.png"/></div>', *c0, calque(ondes)]
    for g, sym, nom in sources:
        x, y = p[g]
        corps.append(f'        <div id="s-{g}" style="position:absolute;left:{x - 34}px;top:{y - 34}px;width:68px;height:68px;border-radius:50%;'
                     'background:#1f6e46;border:3px solid #9ff0c6;box-shadow:0 0 22px rgba(127,224,176,0.8);z-index:5;opacity:0;'
                     f'display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800">{sym}</div>'
                     f'<div id="n-{g}" style="position:absolute;left:{x - 90}px;top:{y + 40}px;width:180px;text-align:center;font-size:24px;'
                     f'font-weight:700;color:#9ff0c6;text-shadow:0 2px 8px #000;z-index:5;opacity:0">{nom}</div>')

    def elements(t, d):
        return [montre(f"#s-{g}", t + 0.3 + 0.5 * k) + "\n" + montre(f"#n-{g}", t + 0.4 + 0.5 * k) for k, (g, _, _) in enumerate(sources)]

    def rayons(t, d):
        lignes = [trace(f"#o-{g}", t + 0.3 + 0.4 * k, 2.0) for k, g in enumerate(("g1", "g2", "g3", "g4"))]
        lignes += [f'      tl.to("#o-{g}", {{ opacity: 0.35, duration: 0.6, repeat: 3, yoyo: true }}, {t + 2.6:.2f});' for g in ("g1", "g2", "g3", "g4")]
        return lignes

    script = ["\n".join(f'      gsap.set("#o-{g}", {{ strokeDasharray: 4000, strokeDashoffset: 4000 }});' for g in ("g1", "g2", "g3", "g4"))]
    c, sc = etapes([
        (2.5, None, None),
        (4.5, "Le cristal a grandi dans une roche", None),
        (4.5, "Cette roche contient des traces<br/>d'éléments radioactifs", elements),
        (5.0, "Leurs rayonnements traversent le cristal<br/>au fil des temps géologiques", rayons),
    ], duree)
    script += [zoom_lent("#i1", duree)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 3. centres colorés : aluminium (fumé, morion) et fer (améthyste)

def centre(duree, assets, fer=False):
    av, ap = ("fe_avant", "fe_apres") if fer else ("al_avant", "al_apres")
    p = copie(av, assets)
    copie(ap, assets)
    al, trou, h = p["al"], p["trou"], p["h"]
    cible = al if fer else trou  # d'où part l'électron
    depart_rayon = (120, 470)
    sym = ("Fe³⁺", "fer") if fer else ("Al³⁺", "aluminium")
    c0, s0 = debut(duree, "Améthyste" if fer else "Morion et quartz fumé", "Le rôle du fer" if fer else "Le centre coloré", MODELE)
    corps = [f'        <div id="p1" class="plan"><img id="i1" src="assets/{av}.png"/></div>',
             f'        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/{ap}.png"/></div>', *c0,
             etiquette("e-al", al, sym[0], sym[1], dx=-40, dy=-200),
             calque(onde("onde", depart_rayon, cible)),
             f'        <div id="electron" style="position:absolute;left:{cible[0] - 16}px;top:{cible[1] - 16}px;width:32px;height:32px;border-radius:50%;'
             'background:radial-gradient(circle,#e8fbff 0%,#5ec8ff 55%,rgba(94,200,255,0) 72%);z-index:5;opacity:0"></div>',
             etiquette("e-e", (cible[0] + 160, cible[1] - 200), "e⁻", "électron", dx=60, dy=-30, cote="droite"),
             etiquette("e-trou", cible, "Centre coloré", "Fe⁴⁺" if fer else "", dx=170, dy=60 if fer else -70, cote="droite")]
    if not fer:
        corps.append(etiquette("e-h", h, "H⁺", "hydrogène", dx=-150, dy=-10, cote="gauche"))

    def rayonnement(t, d):
        return [trace("#onde", t + 0.4, 2.2)]

    def arrache(t, d):
        return ([cache("#onde", t + 0.6, 1.0),
                 '      tl.fromTo("#electron", { opacity: 1, x: 0, y: 0, scale: 1 }, { opacity: 1, x: 160, y: -200, scale: 0.7, duration: 2.0, '
                 'ease: "power1.inOut", immediateRender: false }, %.2f);' % (t + 0.4),
                 montre_etiquette("e-e", t + 2.2),
                 f'      tl.to("#p2", {{ opacity: 1, duration: 1.5, ease: "power2.inOut" }}, {t + 0.5:.2f});']
                + ([] if fer else [cache_etiquette("e-h", t + 0.2)]))

    def colore(t, d):
        return [cache_etiquette("e-e", t), cache("#electron", t), montre_etiquette("e-trou", t + 0.4)] + \
            ([cache_etiquette("e-al", t)] if fer else [])

    if fer:
        liste = [
            (2.5, None, None),
            (4.5, "Des traces de <b>fer</b> prennent parfois<br/>la place du silicium", lambda t, d: [montre_etiquette("e-al", t + 0.3)]),
            (4.0, "Un rayonnement naturel<br/>traverse le cristal", rayonnement),
            (4.5, "L'ion de fer perd un <b>électron</b>", arrache),
            (5.0, "Il devient un <b>centre coloré</b> :<br/>il absorbe une partie de la lumière", colore),
        ]
    else:
        liste = [
            (2.5, None, None),
            (4.5, "Parfois, un atome d'<b>aluminium</b><br/>prend la place d'un silicium", lambda t, d: [montre_etiquette("e-al", t + 0.3)]),
            (4.5, "Il lui manque une charge :<br/>un ion <b>hydrogène</b> la compense", lambda t, d: [montre_etiquette("e-h", t + 0.3)]),
            (4.0, "Un rayonnement naturel<br/>traverse le cristal", rayonnement),
            (4.5, "Il arrache un <b>électron</b><br/>à un oxygène voisin", arrache),
            (5.0, "Cet oxygène devient un <b>centre coloré</b> :<br/>il absorbe la lumière, le quartz fonce", colore),
        ]
    c, sc = etapes(liste, duree)
    script = [zoom_lent("#i1", duree), zoom_lent("#i2", duree), '      gsap.set("#onde", { strokeDasharray: 4000, strokeDashoffset: 4000 });'] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 4. du fumé clair au morion

def gamme(duree, assets):
    p = copie("gamme", assets)
    c0, s0 = debut(duree, "Quartz fumé", "Du gris au noir", ILLU)
    corps = ['        <div class="plan"><img id="i1" src="assets/gamme.png"/></div>', *c0]
    for nom, texte in (("clair", "fumé clair"), ("fume", "fumé"), ("morion", "morion")):
        x, y = p[nom]
        corps.append(f'        <div id="n-{nom}" class="etiquette" style="left:{x}px;top:{y - 10}px;transform:translate(-50%,0);font-size:24px;'
                     f'z-index:5;opacity:0">{texte}</div>')
    noms = ("clair", "fume", "morion")
    c, sc = etapes([
        (2.5, None, None),
        (4.5, "Plus il y a de centres colorés,<br/>plus le quartz est sombre",
         lambda t, d: [montre(f"#n-{n}", t + 0.3 + 0.5 * k) for k, n in enumerate(noms)]),
        (4.5, "Cela dépend de sa teneur en <b>aluminium</b>…", None),
        (4.5, "… et de la <b>dose de rayonnement</b> reçue", None),
        (4.5, "La chaleur, au cours de son histoire,<br/>peut aussi l'éclaircir", None),
    ], duree, haut=1050)
    script = [zoom_lent("#i1", duree)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 5. absorption sélective dans l'améthyste

SPECTRE = ("linear-gradient(90deg,#7a2cff 0%,#2e5bff 16%,#22c7d6 32%,#3ddc5a 46%,#e8e23a 60%,#ff9a2e 78%,#ff3b3b 100%)")


def absorption(duree, assets):
    p = copie("amethyste_faisceau", assets)
    c0, s0 = debut(duree, "Améthyste", "L'absorption sélective", ILLU)
    e, s = p["entree"], p["sortie"]
    corps = ['        <div class="plan"><img id="i1" src="assets/amethyste_faisceau.png"/></div>', *c0,
             calque(rayon("r-in", [(0, e[1] - 30), e]) + rayon("r-dans", [e, s], "#e9d6ff", 7) + rayon("r-out", [s, (1080, s[1] + 30)], "#b86bff")),
             f'        <div id="spectre" style="position:absolute;left:190px;top:880px;width:700px;height:56px;border-radius:12px;'
             f'background:{SPECTRE};box-shadow:0 8px 24px rgba(0,0,0,0.6);z-index:5;opacity:0"></div>',
             '        <div id="absorbe" style="position:absolute;left:470px;top:872px;width:150px;height:72px;border-radius:10px;background:rgba(6,4,10,0.85);'
             'border:3px dashed #f2b544;z-index:6;opacity:0;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#f2b544">absorbé</div>',
             '        <div id="sp-l" style="position:absolute;left:190px;top:946px;width:700px;display:flex;justify-content:space-between;'
             'font-size:20px;font-weight:600;color:#d6d0e0;text-shadow:0 2px 6px #000;z-index:5;opacity:0"><span>violet</span><span>rouge</span></div>']

    def blanche(t, d):
        return [trace("#r-in", t + 0.3, 1.2), montre("#spectre", t + 1.2, 0.6), montre("#sp-l", t + 1.3, 0.6)]

    def absorbe(t, d):
        return [trace("#r-dans", t + 0.3, 1.0), montre("#absorbe", t + 0.8, 0.5)]

    c, sc = etapes([
        (2.5, None, None),
        (4.5, "La lumière blanche contient<br/>toutes les couleurs", blanche),
        (4.5, "Les centres colorés absorbent<br/>surtout le <b>jaune-vert</b>", absorbe),
        (5.0, "Le rouge et le bleu qui ressortent<br/>donnent le <b>violet</b>", lambda t, d: [trace("#r-out", t + 0.3, 1.2)]),
    ], duree)
    script = ['\n'.join(f'      gsap.set("#{r}", {{ strokeDasharray: 4000, strokeDashoffset: 4000 }});' for r in ("r-in", "r-dans", "r-out")),
              zoom_lent("#i1", duree)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 6. quartz laiteux : les inclusions fluides

def laiteux(duree, assets):
    copie("laiteux", assets)
    z = copie("laiteux_zoom", assets)
    c0, s0 = debut(duree, "Quartz laiteux", "La diffusion", ILLU)
    inc, bulle = z["inclusion"], z["bulle"]
    # rayon qui entre, heurte l'inclusion et repart dans plusieurs directions
    eclats = "".join(rayon(f"d{k}", [inc, (inc[0] + 260 * math.cos(math.radians(a)), inc[1] + 260 * math.sin(math.radians(a)))], "#fffbe8", 5)
                     for k, a in enumerate((-150, -95, -40, 15, 70, 125)))
    corps = ['        <div id="p1" class="plan"><img id="i1" src="assets/laiteux.png"/></div>',
             '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/laiteux_zoom.png"/></div>', *c0,
             etiquette("e-liq", inc, "Liquide", "piégé pendant la croissance", dx=-60, dy=-170),
             etiquette("e-gaz", bulle, "Bulle de gaz", "", dx=-40, dy=190, cote="bas"),
             calque(rayon("r-in", [(0, inc[1] - 40), inc], "#fffbe8", 8) + eclats)]
    ids = ["r-in"] + [f"d{k}" for k in range(6)]

    def zoom(t, d):
        return [f'      tl.to("#p2", {{ opacity: 1, duration: 1.4, ease: "power2.inOut" }}, {t:.2f});',
                f'      tl.fromTo("#i2", {{ scale: 1.15 }}, {{ scale: 1.0, duration: {d + 6:.2f}, ease: "power1.out" }}, {t:.2f});',
                montre_etiquette("e-liq", t + 1.6), montre_etiquette("e-gaz", t + 2.4)]

    def diffuse(t, d):
        return [cache_etiquette("e-liq", t), cache_etiquette("e-gaz", t), trace("#r-in", t + 0.3, 1.0)] + \
               [trace(f"#d{k}", t + 1.3 + 0.1 * k, 0.8) for k in range(6)]

    c, sc = etapes([
        (2.5, None, None),
        (4.5, "Il est rempli d'inclusions<br/>microscopiques", None),
        (5.0, "Ce sont surtout de minuscules<br/>gouttes de fluide", zoom),
        (5.0, "Chacune dévie la lumière :<br/>diffusée dans tous les sens, elle paraît blanche", diffuse),
    ], duree)
    script = ['\n'.join(f'      gsap.set("#{r}", {{ strokeDasharray: 4000, strokeDashoffset: 4000 }});' for r in ids),
              zoom_lent("#i1", duree)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 7. cristal de roche : la lumière traverse

def transparence(duree, assets):
    p = copie("transparent", assets)
    c0, s0 = debut(duree, "Cristal de roche", "La transparence", ILLU)
    e, s = p["entree"], p["sortie"]
    corps = ['        <div class="plan"><img id="i1" src="assets/transparent.png"/></div>', *c0,
             calque(rayon("r", [(0, e[1] - 30), e, s, (1080, s[1] + 30)]))]
    c, sc = etapes([
        (2.5, None, None),
        (4.5, "Peu d'impuretés,<br/>peu d'inclusions", None),
        (5.0, "La lumière le traverse<br/>presque sans être absorbée ni dispersée", lambda t, d: [trace("#r", t + 0.3, 2.2)]),
    ], duree)
    script = ['      gsap.set("#r", { strokeDasharray: 4000, strokeDashoffset: 4000 });', zoom_lent("#i1", duree)] + s0 + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


SCENES = {"structure_3d": structure, "irradiation_3d": irradiation, "centre_al_3d": centre,
          "gamme_3d": gamme, "fer_3d": lambda d, a: centre(d, a, fer=True), "absorption_3d": absorption,
          "laiteux_3d": laiteux, "transparence_3d": transparence}
# durée minimale de chaque scène (somme des étapes) ; la synthèse vient de illustrations.py
NOMINAL = {"structure_3d": 23.0, "irradiation_3d": 16.5, "centre_al_3d": 25.0, "gamme_3d": 20.5, "fer_3d": 20.5,
           "absorption_3d": 16.5, "laiteux_3d": 17.0, "transparence_3d": 12.0, "synthese": 9.0}


def composer(nom, duree=None):
    duree = duree or NOMINAL[nom]
    dossier = DOSSIER / nom
    assets = dossier / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (dossier / "index.html").write_text(SCENES[nom](duree, assets), encoding="utf-8")
    (dossier / "meta.json").write_text(json.dumps({"id": nom, "name": nom}), encoding="utf-8")
    (dossier / "package.json").write_text(json.dumps({"name": nom, "private": True, "type": "module"}), encoding="utf-8")
    return dossier


if __name__ == "__main__":
    APERCUS.mkdir(parents=True, exist_ok=True)
    for nom in [a for a in sys.argv[1:] if not a.startswith("-")] or list(SCENES):
        d = composer(nom)
        n = NOMINAL[nom]
        for t in [round(n * f, 1) for f in (0.1, 0.35, 0.6, 0.97)]:
            subprocess.run(["npx", "--yes", VERSION, "snapshot", str(d), "--at", str(t), "--no-end", "-o", str(APERCUS / f"{nom}_{t}")],
                           capture_output=True)
        if "--rendre" in sys.argv:
            subprocess.run(["npx", "--yes", VERSION, "render", str(d), "-q", "delivery", "--fps", "30",
                            "-o", str(ICI / "sources" / "hf" / f"{nom}.mp4"), "--quiet"], check=True)
        print("ok", nom)
