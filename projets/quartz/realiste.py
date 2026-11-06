"""Habillage HyperFrames des rendus réalistes (Blender) : étiquettes pointées sur les atomes, rayonnement, électron.

Les images viennent de blender/scenes.py (sources/rendus/<scène>.png), avec la position des atomes à l'écran
(sources/rendus/<scène>.json). Chaque séquence porte la mention « Modèle 3D ».

python3 projets/quartz/realiste.py                 -> compose et fait un aperçu de chaque séquence à plusieurs instants
python3 projets/quartz/realiste.py --rendre        -> rend aussi les vidéos
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
RENDUS = ICI / "sources" / "rendus"
APERCUS = ICI / "exports" / "apercus_3d"
DUREE = 28.0  # aperçus ; au montage, la durée suit celle du texte lu

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
.etiquette { position:absolute; padding:8px 18px; border-radius:22px; background:rgba(8,6,12,0.82); border:2px solid var(--or);
  font-size:28px; font-weight:800; white-space:nowrap; box-shadow:0 8px 24px rgba(0,0,0,0.6); }
.etiquette small { display:block; font-size:21px; font-weight:600; color:var(--gris); }
.legende { position:absolute; left:110px; width:860px; text-align:center; font-size:30px; font-weight:700; line-height:1.35;
  padding:16px 22px; border-radius:24px; background:rgba(8,6,12,0.78); border:2px solid rgba(199,125,255,0.5); }
.mention { position:absolute; left:110px; top:1150px; width:860px; text-align:right; font-size:20px; font-weight:600; font-style:italic;
  color:rgba(214,208,224,0.85); text-shadow:0 2px 6px #000; }
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
    ancre = {"centre": "translate(-50%,-100%)", "gauche": "translate(-100%,-50%)", "droite": "translate(0,-50%)"}[cote]
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


# ---------------------------------------------------------------- déroulé par étapes
# Une seule information à la fois : chaque étape a sa légende, qui remplace la précédente, et dure au moins 4 s.

def etapes(liste, duree, t0=0.0):
    """liste : [(durée nominale, légende ou None, fonction(t) -> lignes de script)].
    Les durées sont étirées si la séquence est plus longue que prévu. Renvoie (corps, script)."""
    nominal = sum(d for d, _, _ in liste)
    k = max(1.0, (duree - t0) / nominal)
    corps, script, t = [], [], t0
    for n, (d, legende, actions) in enumerate(liste):
        d *= k
        if legende:
            corps.append(f'        <div id="leg{n}" class="legende" style="top:1000px;z-index:5;opacity:0">{legende}</div>')
            script.append(f'      tl.fromTo("#leg{n}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, {t + 0.2:.2f});')
            if n < len(liste) - 1:
                script.append(cache(f"#leg{n}", t + d - 0.45, 0.4))
        if actions:
            script += actions(t, d)
        t += d
    return corps, script


# ---------------------------------------------------------------- 1. structure : un tétraèdre, puis le réseau

def structure(duree, assets):
    p = copie("tetraedre", assets)
    copie("reseau", assets)
    corps = [
        '        <div id="p1" class="plan"><img id="i1" src="assets/tetraedre.png"/></div>',
        '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/reseau.png"/></div>',
        tete("La structure", "Le quartz, SiO₂"),
        etiquette("e-si", p["si"], "Si", "silicium", dx=-190, dy=-40, cote="gauche"),
        etiquette("e-o", p["o1"], "O", "oxygène", dx=150, dy=-60, cote="droite"),
        '        <div class="mention" id="mention" style="z-index:5">Modèle 3D, d\'après la structure cristallographique du quartz α</div>',
    ]
    bascule = []

    def reseau(t, d):
        bascule.append(t)
        return [cache_etiquette("e-si", t), cache_etiquette("e-o", t),
                f'      tl.to("#p2", {{ opacity: 1, duration: 1.4, ease: "power2.inOut" }}, {t:.2f});',
                f'      tl.fromTo("#i2", {{ scale: 1.0, rotation: -3 }}, {{ scale: 1.1, rotation: 3, duration: {duree - t:.2f}, ease: "none" }}, {t:.2f});']

    c, sc = etapes([
        (3.0, None, None),
        (4.5, "Au centre, un atome de <b>silicium</b>", lambda t, d: [montre_etiquette("e-si", t + 0.3)]),
        (4.5, "Autour de lui, quatre atomes d'<b>oxygène</b>", lambda t, d: [montre_etiquette("e-o", t + 0.3)]),
        (4.5, "Ensemble, ils forment un tétraèdre : SiO₄", None),
        (5.0, "Les tétraèdres s'assemblent :<br/>chaque oxygène est partagé entre deux", reseau),
        (5.0, "Ils dessinent des canaux hexagonaux", None),
    ], duree)
    script = ['      tl.fromTo("#i1", { scale: 1.1 }, { scale: 1.0, duration: 21.0, ease: "power1.out" }, 0);',
              montre("#tete", 0.1, 0.6), montre("#mention", 0.6)] + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


# ---------------------------------------------------------------- 2. centre coloré de l'aluminium

def centre_al(duree, assets):
    import math
    p = copie("al_avant", assets)
    copie("al_apres", assets)
    al, trou, h = p["al"], p["trou"], p["h"]
    x0, y0 = 120, 470  # le rayonnement vient du coin supérieur gauche
    dx, dy = trou[0] - x0, trou[1] - y0
    long = math.hypot(dx, dy)
    n = int(long // 34)
    ang = math.degrees(math.atan2(dy, dx))
    vagues = "".join(" q 8.5 -14 17 0 q 8.5 14 17 0" for _ in range(n))
    corps = [
        '        <div id="p1" class="plan"><img id="i1" src="assets/al_avant.png"/></div>',
        '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/al_apres.png"/></div>',
        tete("Morion et quartz fumé", "Le centre coloré"),
        etiquette("e-al", al, "Al³⁺", "aluminium", dx=-40, dy=-200),
        etiquette("e-h", h, "H⁺", "hydrogène", dx=-150, dy=-10, cote="gauche"),
        f'        <svg id="rayon" width="1080" height="1920" style="position:absolute;left:0;top:0;z-index:4">'
        f'<path id="onde" d="M 0 0{vagues}" fill="none" stroke="#7fe0b0" stroke-width="6" stroke-linecap="round" '
        f'transform="translate({x0} {y0}) rotate({ang:.1f}) scale({long / (34 * n):.3f} 1)" style="filter:drop-shadow(0 0 8px #7fe0b0)"/></svg>',
        f'        <div id="electron" style="position:absolute;left:{trou[0] - 16}px;top:{trou[1] - 16}px;width:32px;height:32px;border-radius:50%;'
        'background:radial-gradient(circle,#e8fbff 0%,#5ec8ff 55%,rgba(94,200,255,0) 72%);z-index:5;opacity:0"></div>',
        etiquette("e-e", (trou[0] + 160, trou[1] - 200), "e⁻", "électron", dx=60, dy=-30, cote="droite"),
        etiquette("e-trou", trou, "Centre coloré", "", dx=170, dy=-70, cote="droite"),
        '        <div class="mention" id="mention" style="z-index:5">Modèle 3D, d\'après la structure du quartz α</div>',
    ]
    c, sc = etapes([
        (3.0, None, None),
        (5.0, "Parfois, un atome d'<b>aluminium</b><br/>prend la place d'un silicium", lambda t, d: [montre_etiquette("e-al", t + 0.3)]),
        (5.0, "Il lui manque une charge :<br/>un ion <b>hydrogène</b> la compense", lambda t, d: [montre_etiquette("e-h", t + 0.3)]),
        (4.5, "Un rayonnement naturel<br/>traverse le cristal", lambda t, d: [
            '      tl.fromTo("#onde", { strokeDasharray: 3000, strokeDashoffset: 3000 }, { strokeDashoffset: 0, duration: 2.2, ease: "power1.inOut" }, %.2f);' % (t + 0.4)]),
        (5.0, "Il arrache un <b>électron</b><br/>à un oxygène voisin", lambda t, d: [
            cache_etiquette("e-h", t + 0.2), cache("#onde", t + 0.6, 1.0),
            '      tl.fromTo("#electron", { opacity: 1, x: 0, y: 0, scale: 1 }, { opacity: 1, x: 160, y: -200, scale: 0.7, duration: 2.0, ease: "power1.inOut", immediateRender: false }, %.2f);' % (t + 0.4),
            montre_etiquette("e-e", t + 2.2),
            f'      tl.to("#p2", {{ opacity: 1, duration: 1.5, ease: "power2.inOut" }}, {t + 0.5:.2f});']),
        (5.5, "Cet oxygène devient un <b>centre coloré</b> :<br/>il absorbe la lumière, le quartz fonce", lambda t, d: [
            cache_etiquette("e-e", t), cache("#electron", t), montre_etiquette("e-trou", t + 0.4)]),
    ], duree)
    script = ['      tl.fromTo("#i1", { scale: 1.0 }, { scale: 1.06, duration: %.2f, ease: "none" }, 0);' % duree,
              '      tl.fromTo("#i2", { scale: 1.0 }, { scale: 1.06, duration: %.2f, ease: "none" }, 0);' % duree,
              montre("#tete", 0.1, 0.6), montre("#mention", 0.6)] + sc
    return page(duree, "\n".join(corps + c), "\n".join(script))


SCENES = {"structure_3d": structure, "centre_al_3d": centre_al}


def composer(nom, duree=DUREE):
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
        for t in (2.0, 6.0, 10.5, 15.0, 19.5, 26.5):
            subprocess.run(["npx", "--yes", VERSION, "snapshot", str(d), "--at", str(t), "--no-end", "-o", str(APERCUS / f"{nom}_{t}")],
                           capture_output=True)
        if "--rendre" in sys.argv:
            subprocess.run(["npx", "--yes", VERSION, "render", str(d), "-q", "delivery", "--fps", "30",
                            "-o", str(ICI / "sources" / "hf" / f"{nom}.mp4"), "--quiet"], check=True)
        print("ok", nom)
