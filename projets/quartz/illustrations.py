"""Illustrations schématiques HyperFrames de « Les couleurs du quartz ».

Chaque schéma est posé sur une photo de la collection (assombrie) et porte la mention « Illustration schématique ».
Les durées sont provisoires (aperçus) ; au montage, chaque séquence est recomposée à la durée de son plan.

python3 projets/quartz/illustrations.py            -> compose tout et fait un aperçu (image fixe) de chaque schéma
python3 projets/quartz/illustrations.py --rendre   -> rend aussi les vidéos
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ICI = Path(__file__).resolve().parent
VERSION = "hyperframes@0.8.210"
DOSSIER = ICI / "hyperframes"
SRC = ICI / "sources"
APERCUS = ICI / "exports" / "apercus"
DUREE = 9.0

CSS = """
:root { --violet:#7b2cbf; --violet-clair:#c77dff; --gris:#d6d0e0; --or:#f2b544; --o:#ff6b6b; --si:#9d7bff; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#000; }
#root { position:relative; width:100%; height:100%; font-family:"Montserrat", sans-serif; color:#fff; }
#photo { position:absolute; inset:0; overflow:hidden; }
#photo img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(0.42) saturate(1.0); }
#photo-voile { position:absolute; inset:0;
  background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.15) 30%, rgba(0,0,0,0.25) 60%, rgba(0,0,0,0.8) 100%); }
.tete { position:absolute; top:250px; left:110px; width:860px; text-align:center; }
.surtitre { font-size:30px; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:var(--violet-clair);
  text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.titre { margin-top:14px; font-size:76px; font-weight:800; white-space:nowrap; text-shadow:0 4px 18px rgba(0,0,0,0.7); }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
.panneau { position:absolute; left:110px; top:430px; width:860px; height:640px; background:rgba(8,6,12,0.72);
  border:2px solid rgba(199,125,255,0.55); border-radius:34px; box-shadow:0 24px 60px rgba(0,0,0,0.55); overflow:hidden; }
.schema { position:absolute; left:110px; top:1086px; width:860px; text-align:right; font-size:20px; font-weight:600; color:rgba(214,208,224,0.8); font-style:italic; text-shadow:0 2px 6px #000; }
svg text { font-family:"Montserrat", sans-serif; }
.leg { font-size:26px; font-weight:600; fill:#e8e2f0; }
.leg-or { font-size:28px; font-weight:800; fill:#f2b544; }
"""


def preparer_fond(source, dossier):
    img = Image.open(source).convert("RGB")
    w, h = img.size
    cw = min(w, h * 9 / 16)
    ch = cw * 16 / 9
    img = img.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2))).resize((1080, 1920), Image.LANCZOS)
    (dossier / "assets").mkdir(parents=True, exist_ok=True)
    img.save(dossier / "assets" / "fond.jpg", quality=90)


def page(duree, surtitre, titre, svg, script):
    taille = min(76, int(1500 / max(len(titre), 1)))
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
      <div id="photo" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1"><img id="photo-img" src="assets/fond.jpg" alt="" /><div id="photo-voile"></div></div>
      <div id="scene" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="1" style="z-index:2">
        <div class="tete" id="tete"><div class="surtitre">{surtitre}</div><div class="titre" style="font-size:{taille}px">{titre}</div><div class="filet"></div></div>
        <div class="panneau" id="panneau"><svg width="860" height="640" viewBox="0 0 860 640">{svg}</svg></div>
        <div class="schema" id="schema">Illustration schématique</div>
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#photo-img", {{ scale: 1.0 }}, {{ scale: 1.07, duration: {duree:.2f}, ease: "none" }}, 0);
      tl.fromTo("#tete", {{ opacity: 0, y: -26 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 0.1);
      tl.fromTo("#panneau", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, 0.25);
      tl.fromTo("#schema", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 0.6);
{script}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def pop(sel, t, d=0.4):
    return f'      tl.fromTo("{sel}", {{ opacity: 0, scale: 0.3, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: {d}, ease: "back.out(2)" }}, {t:.2f});'


def montre(sel, t, d=0.45):
    return f'      tl.fromTo("{sel}", {{ opacity: 0 }}, {{ opacity: 1, duration: {d} }}, {t:.2f});'


def trace(sel, t, d=0.6):
    """Tracé progressif d'une ligne ou d'un chemin (stroke-dasharray)."""
    return (f'      tl.fromTo("{sel}", {{ strokeDasharray: 1000, strokeDashoffset: 1000 }}, '
            f'{{ strokeDashoffset: 0, duration: {d}, ease: "power2.out" }}, {t:.2f});')


def atome(ident, x, y, r, couleur, texte, taille=None, texte_couleur="#fff"):
    taille = taille or int(r * 0.9)
    return (f'<g id="{ident}"><circle cx="{x}" cy="{y}" r="{r}" fill="{couleur}" stroke="rgba(255,255,255,0.85)" stroke-width="3"/>'
            f'<text x="{x}" y="{y + taille * 0.36:.1f}" text-anchor="middle" font-size="{taille}" font-weight="800" fill="{texte_couleur}">{texte}</text></g>')


# ---------------------------------------------------------------- 1. SiO2

def sio2():
    cx, cy = 300, 300
    avant = [(300, 112), (150, 400), (450, 400)]
    arriere = (420, 250)  # quatrième oxygène, derrière le silicium (perspective)
    svg = [f'<polygon id="tetra" points="300,112 150,400 450,400" fill="rgba(157,123,255,0.10)" stroke="rgba(199,125,255,0.6)" stroke-width="3"/>',
           f'<g id="arr"><line x1="300" y1="112" x2="{arriere[0]}" y2="{arriere[1]}" stroke="rgba(199,125,255,0.45)" stroke-width="3" stroke-dasharray="10 8"/>'
           f'<line x1="150" y1="400" x2="{arriere[0]}" y2="{arriere[1]}" stroke="rgba(199,125,255,0.45)" stroke-width="3" stroke-dasharray="10 8"/>'
           f'<line x1="450" y1="400" x2="{arriere[0]}" y2="{arriere[1]}" stroke="rgba(199,125,255,0.45)" stroke-width="3" stroke-dasharray="10 8"/>'
           f'<line x1="{cx}" y1="{cy}" x2="{arriere[0]}" y2="{arriere[1]}" stroke="rgba(232,226,240,0.55)" stroke-width="7" stroke-linecap="round"/>'
           f'<g opacity="0.6">{atome("o3", arriere[0], arriere[1], 34, "#d9485a", "O", 30)}</g></g>']
    for i, (x, y) in enumerate(avant):
        svg.append(f'<line id="b{i}" x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#e8e2f0" stroke-width="8" stroke-linecap="round"/>')
    svg.append(atome("si", cx, cy, 52, "#7b2cbf", "Si", 44))
    for i, (x, y) in enumerate(avant):
        svg.append(atome(f"o{i}", x, y, 42, "#d9485a", "O", 38))
    svg += ['<g id="txt">',
            '<text x="650" y="190" text-anchor="middle" font-size="96" font-weight="800" fill="#fff">SiO<tspan font-size="58" dy="18">2</tspan></text>',
            '<text x="650" y="250" text-anchor="middle" class="leg-or">dioxyde de silicium</text>',
            '<text x="650" y="330" text-anchor="middle" class="leg">1 atome de silicium</text>',
            '<text x="650" y="368" text-anchor="middle" class="leg">pour 2 d\'oxygène</text></g>',
            '<g id="txt2"><text x="430" y="500" text-anchor="middle" class="leg">Chaque silicium est au centre de 4 oxygènes,</text>',
            '<text x="430" y="540" text-anchor="middle" class="leg">et chaque oxygène est partagé</text>',
            '<text x="430" y="580" text-anchor="middle" class="leg">entre deux de ces tétraèdres.</text></g>']
    script = [pop("#si", 0.6)] + [trace(f"#b{i}", 0.9 + 0.15 * i) for i in range(3)] + [pop(f"#o{i}", 1.0 + 0.2 * i) for i in range(3)]
    script += [montre("#tetra", 1.8), montre("#arr", 2.0), montre("#txt", 2.2, 0.6), montre("#txt2", 3.4, 0.6)]
    return ("La structure", "Le quartz, SiO₂", "photo_09.jpg", "".join(svg), "\n".join(script))


def onde(x0, y0, x1, y1, ident, couleur="#7fe0b0", larg=4):
    """Rayonnement ondulé de (x0, y0) vers (x1, y1)."""
    dx, dy = x1 - x0, y1 - y0
    long = math.hypot(dx, dy)
    n = max(1, int(long // 30))
    ang = math.degrees(math.atan2(dy, dx))
    vagues = "".join(" q 7.5 -12 15 0 q 7.5 12 15 0" for _ in range(n))
    return (f'<path id="{ident}" d="M 0 0{vagues}" fill="none" stroke="{couleur}" stroke-width="{larg}" stroke-linecap="round" '
            f'transform="translate({x0:.0f} {y0:.0f}) rotate({ang:.1f}) scale({long / (30 * n):.3f} 1)"/>')


# ---------------------------------------------------------------- réseau cristallin (vue simplifiée à plat)

def reseau(centre_couleur, centre_txt, centre_id="centre"):
    """Grille Si–O à plat ; l'atome central est remplacé (Al ou Fe)."""
    svg, nx, ny, pas, x0, y0 = [], 5, 4, 120, 190, 110
    for j in range(ny):
        for i in range(nx):
            x, y = x0 + i * pas, y0 + j * pas
            if i < nx - 1:
                svg.append(f'<line x1="{x}" y1="{y}" x2="{x + pas}" y2="{y}" stroke="rgba(232,226,240,0.45)" stroke-width="4"/>'
                           f'<circle cx="{x + pas / 2}" cy="{y}" r="11" fill="#d9485a"/>')
            if j < ny - 1:
                svg.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + pas}" stroke="rgba(232,226,240,0.45)" stroke-width="4"/>'
                           f'<circle cx="{x}" cy="{y + pas / 2}" r="11" fill="#d9485a"/>')
    for j in range(ny):
        for i in range(nx):
            x, y = x0 + i * pas, y0 + j * pas
            if (i, j) == (2, 1):
                svg.append(f'<g id="si-c"><circle cx="{x}" cy="{y}" r="26" fill="#7b2cbf" stroke="#fff" stroke-width="2"/>'
                           f'<text x="{x}" y="{y + 8}" text-anchor="middle" font-size="22" font-weight="800" fill="#fff">Si</text></g>')
                svg.append(atome(centre_id, x, y, 34, centre_couleur, centre_txt, 26, "#120a00" if centre_couleur == "#f2b544" else "#fff"))
            else:
                svg.append(f'<circle cx="{x}" cy="{y}" r="22" fill="#7b2cbf" stroke="rgba(255,255,255,0.7)" stroke-width="2"/>'
                           f'<text x="{x}" y="{y + 7}" text-anchor="middle" font-size="19" font-weight="700" fill="#fff">Si</text>')
    return "".join(svg), (x0 + 2 * pas, y0 + pas)


def centre_colore(nom, couleur, txt_av, txt_ap, legende1, legende2, photo, surtitre, titre):
    grille, (cx, cy) = reseau(couleur, txt_av)
    svg = [f'<g id="grille">{grille}</g>',
           onde(40, 30, cx - 44, cy - 40, "rayon", larg=5),
           f'<g id="electron"><circle cx="{cx + 46}" cy="{cy - 46}" r="14" fill="#5ec8ff" stroke="#fff" stroke-width="2"/>'
           f'<text x="{cx + 46}" y="{cy - 40}" text-anchor="middle" font-size="16" font-weight="800" fill="#06263a">e⁻</text></g>',
           f'<circle id="halo" cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{couleur}" stroke-width="5" stroke-dasharray="8 8"/>',
           f'<g id="nouveau"><rect x="{cx - 110}" y="{cy + 62}" width="220" height="42" rx="21" fill="rgba(8,6,12,0.92)" stroke="{couleur}" stroke-width="2"/>'
           f'<text x="{cx}" y="{cy + 91}" text-anchor="middle" font-size="24" font-weight="800" fill="{couleur}">{txt_ap}</text></g>',
           f'<g id="l1"><text x="430" y="545" text-anchor="middle" class="leg">{legende1}</text></g>',
           f'<g id="l2"><text x="430" y="590" text-anchor="middle" class="leg-or">{legende2}</text></g>']
    script = [montre("#grille", 0.5, 0.6), "      tl.set(\"#centre\", { opacity: 0 }, 0);",
              montre("#si-c", 0.5), f'      tl.to("#si-c", {{ opacity: 0, duration: 0.4 }}, 1.6);', pop("#centre", 1.6), montre("#l1", 1.7),
              trace("#rayon", 3.0, 0.8), "      tl.set(\"#electron\", { opacity: 0 }, 0);",
              f'      tl.fromTo("#electron", {{ opacity: 1, x: -46, y: 46 }}, {{ x: 220, y: -120, opacity: 0.0, duration: 1.2, ease: "power2.in" }}, 3.8);',
              montre("#halo", 4.2), "      tl.set(\"#nouveau\", { opacity: 0 }, 0);", montre("#nouveau", 4.4),
              f'      tl.fromTo("#halo", {{ scale: 0.9, transformOrigin: "50% 50%" }}, {{ scale: 1.12, duration: 0.8, repeat: 4, yoyo: true, ease: "sine.inOut" }}, 4.4);',
              montre("#l2", 5.0)]
    return (surtitre, titre, photo, "".join(svg), "\n".join(script))


def aluminium():
    return centre_colore("aluminium", "#f2b544", "Al", "centre coloré",
                         "L'aluminium remplace parfois le silicium.",
                         "Le rayonnement arrache un électron : centre coloré",
                         "photo_02.jpg", "Morion et quartz fumé", "Le centre coloré")


def fer():
    return centre_colore("fer", "#c77dff", "Fe", "centre coloré",
                         "Des traces de fer remplacent parfois le silicium.",
                         "Le rayonnement arrache un électron au fer",
                         "photo_06.jpg", "Améthyste", "Le rôle du fer")


# ---------------------------------------------------------------- 2. irradiation naturelle

def irradiation():
    svg = ['<rect x="0" y="0" width="860" height="640" fill="#2a2228"/>',
           # roche : grain
           ''.join(f'<circle cx="{(i * 97) % 860}" cy="{(i * 53) % 640}" r="{3 + i % 5}" fill="rgba(255,255,255,{0.04 + (i % 3) * 0.03})"/>' for i in range(160)),
           # cristal de quartz (prisme + pointe), au centre
           '<polygon id="cristal" points="360,520 360,250 430,150 500,250 500,520" fill="rgba(220,215,230,0.18)" stroke="#e8e2f0" stroke-width="4"/>',
           '<line x1="430" y1="150" x2="430" y2="520" stroke="rgba(232,226,240,0.35)" stroke-width="2"/>',
           '<text id="t-cristal" x="430" y="560" text-anchor="middle" class="leg">cristal de quartz</text>']
    sources = [("U", "uranium", 130, 170), ("Th", "thorium", 720, 200), ("K", "potassium", 150, 470), ("U", "", 700, 480)]
    for k, (sym, nom, x, y) in enumerate(sources):
        svg.append(atome(f"src{k}", x, y, 34, "#2f8f5b", sym, 28))
        if nom:
            svg.append(f'<text id="n{k}" x="{x}" y="{y + 62}" text-anchor="middle" font-size="22" font-weight="600" fill="#9ff0c6">{nom}</text>')
        tx = 400 if x < 430 else 460
        ty = 260 + (y - 170) * 0.6
        dx, dy = tx - x, ty - y
        long = math.hypot(dx, dy)
        n = int(long // 30)
        ang = math.degrees(math.atan2(dy, dx))
        onde = "".join(" q 7.5 -12 15 0 q 7.5 12 15 0" for _ in range(n))
        svg.append(f'<path id="r{k}" d="M 0 0{onde}" fill="none" stroke="#7fe0b0" stroke-width="4" transform="translate({x + 38 * dx / long:.0f} {y + 38 * dy / long:.0f}) rotate({ang:.1f})"/>')
    svg.append('<g id="leg"><text x="430" y="60" text-anchor="middle" class="leg">Les roches voisines contiennent des éléments radioactifs.</text>'
               '<text x="430" y="610" text-anchor="middle" class="leg-or">Leurs rayonnements traversent le cristal</text></g>')
    script = [montre("#cristal", 0.5), montre("#t-cristal", 0.7)]
    for k in range(4):
        script.append(pop(f"#src{k}", 1.2 + 0.25 * k))
        script.append(montre(f"#n{k}", 1.4 + 0.25 * k) if k < 3 else "")
        script.append(trace(f"#r{k}", 2.6 + 0.3 * k, 1.0))
        script.append(f'      tl.to("#r{k}", {{ opacity: 0.35, duration: 0.5, repeat: 5, yoyo: true }}, {3.8 + 0.3 * k:.2f});')
    script.append(montre("#leg", 1.0))
    return ("Morion", "L'irradiation naturelle", "photo_01.jpg", "".join(svg), "\n".join(s for s in script if s))


# ---------------------------------------------------------------- 4. du fumé au morion

def gamme():
    svg = ['<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#d9d4cc"/><stop offset="0.35" stop-color="#9a8268"/>'
           '<stop offset="0.7" stop-color="#4a3424"/><stop offset="1" stop-color="#0c0908"/></linearGradient></defs>',
           '<rect id="barre" x="60" y="90" width="740" height="110" rx="22" fill="url(#g)" stroke="rgba(255,255,255,0.6)" stroke-width="2"/>',
           '<g id="eti"><text x="110" y="250" text-anchor="middle" class="leg">gris clair</text><text x="430" y="250" text-anchor="middle" class="leg">brun</text>'
           '<text x="750" y="250" text-anchor="middle" class="leg">noir</text>'
           '<text x="250" y="295" text-anchor="middle" class="leg-or">quartz fumé</text><text x="720" y="295" text-anchor="middle" class="leg-or">morion</text></g>',
           '<text id="q" x="430" y="370" text-anchor="middle" font-size="30" font-weight="800" fill="#fff">L\'intensité dépend :</text>']
    items = [("de la composition du cristal", "teneur en aluminium"), ("de la dose de rayonnement reçue", "intensité, durée"),
             ("de son histoire géologique", "chaleur, âge")]
    for k, (a, b) in enumerate(items):
        y = 430 + 62 * k
        svg.append(f'<g id="i{k}"><circle cx="120" cy="{y - 9}" r="10" fill="#c77dff"/><text x="150" y="{y}" class="leg">{a}</text></g>')
    script = [f'      tl.fromTo("#barre", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 1.4, ease: "power2.inOut" }}, 0.6);',
              montre("#eti", 1.8), montre("#q", 2.6)] + [montre(f"#i{k}", 3.0 + 0.5 * k) for k in range(3)]
    return ("Quartz fumé", "Du gris au noir", "photo_04.jpg", "".join(svg), "\n".join(script))


# ---------------------------------------------------------------- 6. absorption sélective

def absorption():
    spectre = ('<defs><linearGradient id="sp" x1="0" x2="1">'
               '<stop offset="0" stop-color="#7a2cff"/><stop offset="0.18" stop-color="#2e5bff"/><stop offset="0.36" stop-color="#22c7d6"/>'
               '<stop offset="0.5" stop-color="#3ddc5a"/><stop offset="0.64" stop-color="#e8e23a"/><stop offset="0.8" stop-color="#ff9a2e"/>'
               '<stop offset="1" stop-color="#ff3b3b"/></linearGradient></defs>')
    svg = [spectre,
           '<g id="entree"><rect x="40" y="150" width="210" height="44" rx="10" fill="#fff"/><polygon points="248,132 288,172 248,212" fill="#fff"/><text x="155" y="130" text-anchor="middle" class="leg">lumière blanche</text></g>',
           '<polygon id="cri" points="300,320 300,110 360,40 420,110 420,320" fill="rgba(157,92,220,0.55)" stroke="#e8e2f0" stroke-width="4"/>',
           '<g id="sortie"><rect x="450" y="150" width="230" height="44" rx="10" fill="#9b5de5"/>'
           '<polygon points="680,132 720,172 680,212" fill="#9b5de5"/><text x="580" y="130" text-anchor="middle" class="leg">violet</text></g>',
           '<rect id="spectre" x="80" y="400" width="700" height="70" rx="12" fill="url(#sp)"/>',
           '<g id="abs"><rect x="370" y="392" width="170" height="86" rx="10" fill="rgba(0,0,0,0.78)" stroke="#f2b544" stroke-width="3" stroke-dasharray="8 6"/>'
           '<text x="455" y="443" text-anchor="middle" font-size="24" font-weight="800" fill="#f2b544">absorbé</text></g>',
           '<g id="l"><text x="430" y="530" text-anchor="middle" class="leg">Le centre coloré absorbe le jaune-vert ;</text>'
           '<text x="430" y="572" text-anchor="middle" class="leg">le rouge et le bleu restants donnent le violet.</text></g>',
           '<text x="80" y="505" font-size="20" fill="#d6d0e0">violet</text><text x="780" y="505" text-anchor="end" font-size="20" fill="#d6d0e0">rouge</text>']
    script = [montre("#cri", 0.5), f'      tl.fromTo("#entree", {{ opacity: 0, x: -60 }}, {{ opacity: 1, x: 0, duration: 0.6 }}, 1.0);',
              montre("#spectre", 1.8, 0.6), pop("#abs", 2.8), f'      tl.fromTo("#sortie", {{ opacity: 0, x: -60 }}, {{ opacity: 1, x: 0, duration: 0.6 }}, 3.6);',
              montre("#l", 4.4, 0.6)]
    return ("Améthyste", "L'absorption sélective", "photo_07.jpg", "".join(svg), "\n".join(script))


# ---------------------------------------------------------------- 7 et 8. diffusion (laiteux) et transparence

def lumiere(laiteux):
    svg = ['<polygon id="cri" points="250,560 250,200 430,70 610,200 610,560" fill="rgba(235,235,240,{})" stroke="#e8e2f0" stroke-width="4"/>'.format(0.22 if laiteux else 0.06)]
    rayons = []
    bulles = [(330, 250), (480, 230), (390, 330), (540, 350), (300, 420), (450, 450), (560, 480), (360, 510), (500, 300), (420, 400)]
    for k, y in enumerate((260, 340, 420, 500)):
        if laiteux:
            # le rayon entre, rencontre une inclusion et part dans plusieurs directions
            bx, by = bulles[k * 2 + 1] if k * 2 + 1 < len(bulles) else bulles[k]
            rayons.append(f'<path id="ray{k}" d="M 40 {y} L 250 {y} L {bx} {by}" fill="none" stroke="#fff6c8" stroke-width="6" stroke-linecap="round"/>')
            for m, ang in enumerate((-70, -20, 35, 80, 140)):
                ex, ey = bx + 120 * math.cos(math.radians(ang + 30 * k)), by + 120 * math.sin(math.radians(ang + 30 * k))
                rayons.append(f'<line id="d{k}_{m}" x1="{bx}" y1="{by}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="rgba(255,246,200,0.75)" stroke-width="3" stroke-linecap="round"/>')
        else:
            rayons.append(f'<path id="ray{k}" d="M 40 {y} L 820 {y}" fill="none" stroke="#fff6c8" stroke-width="6" stroke-linecap="round"/>')
    svg += rayons
    if laiteux:
        for k, (x, y) in enumerate(bulles):
            svg.append(f'<g id="bu{k}"><circle cx="{x}" cy="{y}" r="16" fill="rgba(160,210,255,0.35)" stroke="#fff" stroke-width="2"/>'
                       f'<circle cx="{x + 5}" cy="{y - 5}" r="5" fill="rgba(255,255,255,0.9)"/></g>')
        svg.append('<g id="l"><text x="430" y="40" text-anchor="middle" class="leg">Inclusions fluides : du liquide et une bulle de gaz</text>'
                   '<text x="430" y="610" text-anchor="middle" class="leg-or">La lumière est diffusée : le quartz paraît blanc</text></g>')
    else:
        svg.append('<g id="l"><text x="430" y="40" text-anchor="middle" class="leg">Peu d\'impuretés, peu d\'inclusions</text>'
                   '<text x="430" y="610" text-anchor="middle" class="leg-or">La lumière traverse presque sans être dispersée</text></g>')
    script = [montre("#cri", 0.5)]
    if laiteux:
        script += [pop(f"#bu{k}", 1.0 + 0.12 * k, 0.3) for k in range(len(bulles))]
    for k in range(4):
        script.append(trace(f"#ray{k}", 2.4 + 0.35 * k, 0.9))
        if laiteux:
            script += [trace(f"#d{k}_{m}", 3.2 + 0.35 * k, 0.5) for m in range(5)]
    script.append(montre("#l", 1.0 if laiteux else 0.8, 0.6))
    return (("Quartz laiteux", "La diffusion", "photo_11.jpg") if laiteux else ("Cristal de roche", "La transparence", "photo_09.jpg")) + ("".join(svg), "\n".join(script))


# ---------------------------------------------------------------- 9. synthèse

def synthese():
    cartes = [("Morion", "rayonnement + aluminium", "photo_01.jpg"), ("Fumé", "rayonnement + aluminium", "photo_04.jpg"),
              ("Améthyste", "rayonnement + fer", "photo_06.jpg"), ("Laiteux", "inclusions fluides", "photo_11.jpg"),
              ("Cristal de roche", "pureté", "photo_09.jpg")]
    svg = []
    for k, (nom, cause, ph) in enumerate(cartes):
        y = 30 + 118 * k
        svg.append(f'<g id="c{k}"><clipPath id="cp{k}"><circle cx="90" cy="{y + 50}" r="46"/></clipPath>'
                   f'<image href="assets/{ph}" x="44" y="{y + 4}" width="92" height="92" preserveAspectRatio="xMidYMid slice" clip-path="url(#cp{k})"/>'
                   f'<circle cx="90" cy="{y + 50}" r="46" fill="none" stroke="#f2b544" stroke-width="4"/>'
                   f'<text x="170" y="{y + 42}" font-size="32" font-weight="800" fill="#fff">{nom}</text>'
                   f'<text x="170" y="{y + 80}" font-size="25" font-weight="600" fill="#f2b544">{cause}</text></g>')
    script = [f'      tl.fromTo("#c{k}", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {0.8 + 0.5 * k:.2f});' for k in range(5)]
    return ("Une même formule, SiO₂", "Cinq histoires", "photo_08.jpg", "".join(svg), "\n".join(script))


SCENES = {"sio2": sio2, "irradiation": irradiation, "aluminium": aluminium, "gamme": gamme, "fer": fer,
          "absorption": absorption, "laiteux": lambda: lumiere(True), "transparence": lambda: lumiere(False), "synthese": synthese}


def composer(nom, duree=DUREE):
    surtitre, titre, photo, svg, script = SCENES[nom]()
    dossier = DOSSIER / nom
    preparer_fond(SRC / photo, dossier)
    if nom == "synthese":
        for ph in ("photo_01.jpg", "photo_04.jpg", "photo_06.jpg", "photo_11.jpg", "photo_09.jpg"):
            Image.open(SRC / ph).convert("RGB").resize((400, int(400 * 4 / 3))).save(dossier / "assets" / ph, quality=88)
    (dossier / "index.html").write_text(page(duree, surtitre, titre, svg, script), encoding="utf-8")
    (dossier / "meta.json").write_text(json.dumps({"id": nom, "name": nom}), encoding="utf-8")
    (dossier / "package.json").write_text(json.dumps({"name": nom, "private": True, "type": "module"}), encoding="utf-8")
    return dossier


if __name__ == "__main__":
    APERCUS.mkdir(parents=True, exist_ok=True)
    noms = [a for a in sys.argv[1:] if not a.startswith("-")] or list(SCENES)
    for nom in noms:
        d = composer(nom)
        subprocess.run(["npx", "--yes", VERSION, "snapshot", str(d), "--at", f"{DUREE - 0.3}", "--no-end",
                        "-o", str(APERCUS / nom)], capture_output=True)
        if "--rendre" in sys.argv:
            subprocess.run(["npx", "--yes", VERSION, "render", str(d), "-q", "delivery", "--fps", "30",
                            "-o", str(SRC / "hf" / f"{nom}.mp4"), "--quiet"], check=True)
        print("ok", nom)
