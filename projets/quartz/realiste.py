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
DUREE = 10.0

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


# ---------------------------------------------------------------- 1. structure : un tétraèdre, puis le réseau

def structure(duree, assets):
    p = copie("tetraedre", assets)
    copie("reseau", assets)
    bascule = duree * 0.48
    corps = [
        '        <div id="p1" class="plan"><img id="i1" src="assets/tetraedre.png"/></div>',
        '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/reseau.png"/></div>',
        tete("La structure", "Le quartz, SiO₂"),
        etiquette("e-si", p["si"], "Si", "silicium", dx=-190, dy=-40, cote="gauche"),
        etiquette("e-o", p["o1"], "O", "oxygène", dx=150, dy=-60, cote="droite"),
        '        <div id="l1" class="legende" style="top:1010px;z-index:5;opacity:0">Un silicium au centre de 4 oxygènes : le tétraèdre SiO₄</div>',
        '        <div id="l2" class="legende" style="top:980px;z-index:5;opacity:0">Chaque oxygène relie deux tétraèdres :<br/>le réseau forme des canaux hexagonaux</div>',
        '        <div class="mention" id="mention" style="z-index:5">Modèle 3D, d\'après la structure cristallographique du quartz α</div>',
    ]
    script = [
        '      tl.fromTo("#i1", { scale: 1.12 }, { scale: 1.0, duration: %.2f, ease: "power1.out" }, 0);' % (bascule + 0.6),
        '      tl.fromTo("#i2", { scale: 1.0, rotation: -4 }, { scale: 1.12, rotation: 4, duration: %.2f, ease: "none" }, %.2f);' % (duree - bascule, bascule),
        montre("#tete", 0.1, 0.6), montre("#mention", 0.6),
        montre_etiquette("e-si", 0.9), montre_etiquette("e-o", 1.3), montre("#l1", 1.8, 0.5),
        cache_etiquette("e-si", bascule - 0.3), cache_etiquette("e-o", bascule - 0.3), cache("#l1", bascule - 0.3),
        f'      tl.to("#p2", {{ opacity: 1, duration: 0.9, ease: "power2.inOut" }}, {bascule:.2f});',
        montre("#l2", bascule + 0.8, 0.5),
    ]
    return page(duree, "\n".join(corps), "\n".join(script))


# ---------------------------------------------------------------- 2. centre coloré de l'aluminium

def centre_al(duree, assets):
    p = copie("al_avant", assets)
    copie("al_apres", assets)
    al, trou, h = p["al"], p["trou"], p["h"]
    t_rayon = duree * 0.38
    t_apres = t_rayon + 1.3
    # onde du rayonnement : du coin supérieur gauche jusqu'à l'oxygène
    x0, y0 = 120, 470
    dx, dy = trou[0] - x0, trou[1] - y0
    import math
    long = math.hypot(dx, dy)
    n = int(long // 34)
    ang = math.degrees(math.atan2(dy, dx))
    vagues = "".join(" q 8.5 -14 17 0 q 8.5 14 17 0" for _ in range(n))
    corps = [
        '        <div id="p1" class="plan"><img id="i1" src="assets/al_avant.png"/></div>',
        '        <div id="p2" class="plan" style="opacity:0"><img id="i2" src="assets/al_apres.png"/></div>',
        tete("Morion et quartz fumé", "Le centre coloré"),
        etiquette("e-al", al, "Al³⁺", "à la place d'un Si⁴⁺", dx=-40, dy=-200),
        etiquette("e-h", h, "H⁺", "compense la charge", dx=-30, dy=200),
        f'        <svg id="rayon" width="1080" height="1920" style="position:absolute;left:0;top:0;z-index:4">'
        f'<path id="onde" d="M 0 0{vagues}" fill="none" stroke="#7fe0b0" stroke-width="6" stroke-linecap="round" '
        f'transform="translate({x0} {y0}) rotate({ang:.1f}) scale({long / (34 * n):.3f} 1)" style="filter:drop-shadow(0 0 8px #7fe0b0)"/></svg>',
        f'        <div id="electron" style="position:absolute;left:{trou[0] - 16}px;top:{trou[1] - 16}px;width:32px;height:32px;border-radius:50%;'
        'background:radial-gradient(circle,#e8fbff 0%,#5ec8ff 55%,rgba(94,200,255,0) 72%);z-index:5;opacity:0"></div>',
        etiquette("e-e", (trou[0] + 160, trou[1] - 200), "e⁻", "électron arraché", dx=60, dy=-30, cote="droite"),
        etiquette("e-trou", trou, "Centre coloré", "un oxygène a perdu<br/>un électron", dx=170, dy=-70, cote="droite"),
        '        <div id="l1" class="legende" style="top:1000px;z-index:5;opacity:0">Le rayonnement arrache un électron<br/>à un oxygène voisin de l\'aluminium</div>',
        '        <div class="mention" id="mention" style="z-index:5">Modèle 3D, d\'après la structure du quartz α</div>',
    ]
    script = [
        '      tl.fromTo("#i1", { scale: 1.0 }, { scale: 1.06, duration: %.2f, ease: "none" }, 0);' % duree,
        '      tl.fromTo("#i2", { scale: 1.0 }, { scale: 1.06, duration: %.2f, ease: "none" }, 0);' % duree,
        montre("#tete", 0.1, 0.6), montre("#mention", 0.6),
        montre_etiquette("e-al", 0.8), montre_etiquette("e-h", 1.4),
        '      tl.fromTo("#onde", { strokeDasharray: 3000, strokeDashoffset: 3000 }, { strokeDashoffset: 0, duration: 0.9, ease: "power2.in" }, %.2f);' % t_rayon,
        cache_etiquette("e-h", t_rayon), montre("#l1", t_rayon, 0.5),
        '      tl.fromTo("#electron", { opacity: 1, x: 0, y: 0, scale: 1 }, { x: 160, y: -200, scale: 0.7, duration: 1.1, ease: "power2.out" }, %.2f);' % (t_rayon + 0.9),
        montre_etiquette("e-e", t_rayon + 1.6),
        f'      tl.to("#p2", {{ opacity: 1, duration: 0.8, ease: "power2.inOut" }}, {t_apres:.2f});',
        cache("#onde", t_apres + 0.3, 0.6),
        cache_etiquette("e-e", t_apres + 2.0), cache("#electron", t_apres + 2.0),
        montre_etiquette("e-trou", t_apres + 0.9),
    ]
    return page(duree, "\n".join(corps), "\n".join(script))


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
        for t in (2.5, 4.6, 6.0, 9.5):
            subprocess.run(["npx", "--yes", VERSION, "snapshot", str(d), "--at", str(t), "--no-end", "-o", str(APERCUS / f"{nom}_{t}")],
                           capture_output=True)
        if "--rendre" in sys.argv:
            subprocess.run(["npx", "--yes", VERSION, "render", str(d), "-q", "delivery", "--fps", "30",
                            "-o", str(ICI / "sources" / "hf" / f"{nom}.mp4"), "--quiet"], check=True)
        print("ok", nom)
