"""Séquences HyperFrames de la vidéo « L'uranium français ».

Compteurs dès qu'un chiffre apparaît, fiches chimiques sur fond de la photo du minéral, carte de prudence.
Chaque séquence est composée à la durée exacte de son plan et calée sur les mots du texte.

python3 projets/uranium/hyperframes_scenes.py               -> compose et rend tout
python3 projets/uranium/hyperframes_scenes.py fiche_autunite -> une seule séquence
python3 projets/uranium/hyperframes_scenes.py --check       -> compose et vérifie sans rendre

Faits affichés : voir RECHERCHES.md et SOURCES.md (formules et duretés : Wikipédia, Frondel 1951 pour la sabugalite ;
tonnages et dates : inventaire MIMAUSA de l'IRSN, DREAL, bilan AREVA Aveyron ; ouraline : Corning Museum of Glass).
"""
import json
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
:root { --fond-haut:#0b0710; --fond-bas:#1a0f2a; --violet:#7b2cbf; --violet-clair:#c77dff; --gris:#c3bdd0; --uranium:#d4f25a; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:var(--fond-haut); }
#root { position:relative; width:100%; height:100%; font-family:"Montserrat", sans-serif; color:#fff; }
#fond { position:absolute; inset:0;
  background: radial-gradient(900px 700px at 50% 34%, rgba(123,44,191,0.22), rgba(0,0,0,0) 70%),
              linear-gradient(180deg, var(--fond-haut), var(--fond-bas)); }
#photo { position:absolute; inset:0; overflow:hidden; }
#photo img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(0.5) saturate(1.05); }
#photo-voile { position:absolute; inset:0;
  background: linear-gradient(180deg, rgba(11,7,16,0.55) 0%, rgba(11,7,16,0.15) 30%, rgba(11,7,16,0.25) 60%, rgba(11,7,16,0.75) 100%); }
/* zone utile : x 110-970, y 250-1120 (au-dessus des sous-titres, hors marges des réseaux) */
.tete { position:absolute; top:250px; left:110px; width:860px; text-align:center; }
.surtitre { font-size:30px; font-weight:600; letter-spacing:0.18em; text-transform:uppercase; color:var(--violet-clair); }
.titre { margin-top:14px; font-size:80px; font-weight:800; letter-spacing:-0.01em; text-shadow:0 4px 18px rgba(0,0,0,0.6); }
.filet { width:120px; height:8px; margin:22px auto 0; border-radius:4px; background:var(--violet-clair); }
.grand { font-weight:800; line-height:1; color:var(--violet-clair); font-variant-numeric:tabular-nums; letter-spacing:-0.03em; }
.unite { font-size:50px; font-weight:700; }
.petit { font-size:34px; font-weight:600; color:var(--gris); }
.periode { position:absolute; left:150px; width:780px; }
.barre { position:relative; height:22px; border-radius:11px; background:rgba(255,255,255,0.12); overflow:hidden; }
.barre-plein { position:absolute; inset:0; border-radius:11px; background:linear-gradient(90deg, var(--violet), var(--violet-clair)); transform-origin:left center; }
.bornes { display:flex; justify-content:space-between; margin-top:14px; font-size:36px; font-weight:700; color:var(--gris); }
.badge { display:inline-block; padding:12px 26px; border-radius:40px; font-size:32px; font-weight:700;
  background:rgba(123,44,191,0.28); border:2px solid rgba(199,125,255,0.7); }
"""

ELEMENTS = {"U": "uranium", "Ca": "calcium", "Cu": "cuivre", "Al": "aluminium", "Si": "silicium",
            "P": "phosphore", "O": "oxygène", "H": "hydrogène"}

FICHES = {
    "sabugalite": dict(nom="Sabugalite", photo="photo_01.jpg",
                       formule="HAl(UO<sub>2</sub>)<sub>4</sub>(PO<sub>4</sub>)<sub>4</sub>·16H<sub>2</sub>O", taille=56,
                       fluo="Fluorescente sous ultraviolet", elements=["H", "Al", "U", "P", "O"], durete=(2.5, 2.5), durete_txt="2,5"),
    "autunite": dict(nom="Autunite", photo="photo_03.jpg",
                     formule="Ca(UO<sub>2</sub>)<sub>2</sub>(PO<sub>4</sub>)<sub>2</sub>·10-12H<sub>2</sub>O", taille=56,
                     fluo="Fluorescence vert vif sous ultraviolet", elements=["Ca", "U", "P", "O", "H"], durete=(2, 2.5), durete_txt="2 à 2,5"),
    "uranophane": dict(nom="Uranophane", photo="photo_05.jpg",
                       formule="Ca(UO<sub>2</sub>)<sub>2</sub>(SiO<sub>3</sub>OH)<sub>2</sub>·5H<sub>2</sub>O", taille=58,
                       fluo="Faible fluorescence vert-jaune", elements=["Ca", "U", "Si", "O", "H"], durete=(2.5, 2.5), durete_txt="2,5"),
    "torbernite": dict(nom="Torbernite", photo="photo_07.jpg",
                       formule="Cu(UO<sub>2</sub>)<sub>2</sub>(PO<sub>4</sub>)<sub>2</sub>·12H<sub>2</sub>O", taille=62,
                       fluo="Non fluorescente", elements=["Cu", "U", "P", "O", "H"], durete=(2, 2.5), durete_txt="2 à 2,5"),
}


def page(duree, corps, css, script, photo=None):
    if photo:
        fond = (f'      <div id="photo" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1">'
                f'<img id="photo-img" src="assets/fond.jpg" alt="" /><div id="photo-voile"></div></div>')
        lent = f'      tl.fromTo("#photo-img", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {duree:.2f}, ease: "none" }}, 0);\n'
    else:
        fond = f'      <div id="fond" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="0" style="z-index:1"></div>'
        lent = ""
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
{fond}
      <div id="scene" class="clip" data-start="0" data-duration="{duree:.2f}" data-track-index="1" style="z-index:2">
{corps}
      </div>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // lente avancée de caméra sur toute la séquence
      tl.fromTo("#scene", {{ scale: 1 }}, {{ scale: 1.03, duration: {duree:.2f}, ease: "none" }}, 0);
{lent}{script}
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


def compteur(sel, depart, arrivee, t, d, decimales=0, separateur=True, prefixe="", suffixe=""):
    """Compteur animé, au format français (espace insécable fine pour les milliers, virgule décimale)."""
    var = sel.strip("#").replace("-", "_")
    fmt = ("v.toFixed(%d).replace('.', ',')" % decimales) if decimales else "Math.round(v).toString()"
    milliers = ".replace(/\\B(?=(\\d{3})+(?!\\d))/g, '\\u202f')" if separateur else ""
    return f"""      const {var} = {{ v: {depart} }};
      tl.fromTo({var}, {{ v: {depart} }}, {{ v: {arrivee}, duration: {d:.2f}, ease: "power2.out",
        onUpdate: () => {{ const v = {var}.v; document.querySelector("{sel}").textContent = "{prefixe}" + {fmt}{milliers} + "{suffixe}"; }} }}, {t:.2f});"""


def periode(ident, top, debut, fin, t, d):
    corps = (f'        <div class="periode" id="{ident}" style="top:{top}px"><div class="barre"><div class="barre-plein" id="{ident}-plein"></div></div>'
             f'<div class="bornes"><span>{debut}</span><span>{fin}</span></div></div>')
    script = (apparition(f"#{ident}", t, 12, 0.4) + "\n" +
              f'      tl.fromTo("#{ident}-plein", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {d:.2f}, ease: "power2.out" }}, {t + 0.1:.2f});')
    return corps, script


# ---------------------------------------------------------------- scènes chiffrées

def cea_1945(duree, t2):
    corps = [tete("La chasse à l'uranium", "Le CEA s'organise"),
             '        <div id="annee" class="grand" style="position:absolute;top:560px;width:100%;text-align:center;font-size:260px">1930</div>',
             '        <div id="legende" class="petit" style="position:absolute;top:860px;width:100%;text-align:center">École de prospection du CEA</div>',
             '        <div id="date" style="position:absolute;top:930px;width:100%;text-align:center"><span class="badge">2 décembre 1945</span></div>']
    script = [ENTREE_TETE, apparition("#annee", 0.3, 30),
              compteur("#annee", 1930, 1945, 0.4, 1.6, separateur=False),
              apparition("#legende", 1.6), apparition("#date", min(2.0, t2))]
    return page(duree, "\n".join(corps), "", "\n".join(script))


def france_bilan(duree):
    corps = [tete("France · 1948-2001", "L'uranium français"),
             '        <div id="c1" style="position:absolute;top:500px;left:110px;width:430px;text-align:center"><div id="sites" class="grand" style="font-size:150px">0</div><div class="unite">sites</div></div>',
             '        <div id="c2" style="position:absolute;top:500px;left:540px;width:430px;text-align:center"><div id="tonnes" class="grand" style="font-size:96px;padding-top:34px;white-space:nowrap">0</div><div class="unite">t d\'uranium</div></div>']
    p_corps, p_script = periode("per", 900, "1948", "2001", 0.6, 2.4)
    corps.append(p_corps)
    script = [ENTREE_TETE, apparition("#c1", 0.3, 30), apparition("#c2", 0.45, 30),
              compteur("#sites", 0, 250, 0.45, 2.0), compteur("#tonnes", 0, 80000, 0.6, 2.4, prefixe="≈ "), p_script]
    return page(duree, "\n".join(corps), "", "\n".join(script))


def tonnage(duree, surtitre, titre, valeur, decimales, prefixe, debut, fin, badges, t_chiffre=0.5, comparaison=None):
    corps = [tete(surtitre, titre),
             f'        <div id="mesure" style="position:absolute;top:500px;left:110px;width:860px;text-align:center">'
             f'<div id="nombre" class="grand" style="font-size:210px">0</div><div class="unite">tonnes d\'uranium</div></div>']
    p_corps, p_script = periode("per", 840, debut, fin, t_chiffre + 0.2, 2.2)
    corps.append(p_corps)
    corps.append('        <div id="badges" style="position:absolute;top:990px;left:110px;width:860px;text-align:center">' +
                 " ".join(f'<span class="badge" style="margin:0 8px">{b}</span>' for b in badges) + '</div>')
    script = [ENTREE_TETE, apparition("#mesure", t_chiffre, 30),
              compteur("#nombre", 0, valeur, t_chiffre + 0.1, 2.2, decimales=decimales, prefixe=prefixe), p_script,
              apparition("#badges", t_chiffre + 1.2)]
    if comparaison:  # barres à la même échelle : Margnac contre ce site
        t = comparaison
        corps[-1] = corps[-1].replace("top:990px", "top:1120px;display:none")
        corps.append('        <div id="comp" style="position:absolute;top:990px;left:150px;width:780px">'
                     '<div class="petit" style="font-size:28px;margin-bottom:8px">Margnac · 9 454 t</div>'
                     '<div class="barre" style="height:26px"><div class="barre-plein" id="comp-a"></div></div>'
                     f'<div class="petit" style="font-size:28px;margin:14px 0 8px">{titre} · {str(valeur).replace(".", ",")} t</div>'
                     '<div class="barre" style="height:26px"><div class="barre-plein" id="comp-b" style="width:'
                     f'{max(valeur / 9454 * 100, 0.25):.3f}%;background:var(--uranium)"></div></div></div>')
        script = script[:-1] + [apparition("#comp", t, 12, 0.4),
                                f'      tl.fromTo("#comp-a", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.2, ease: "power2.out" }}, {t + 0.1:.2f});',
                                f'      tl.fromTo("#comp-b", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, {t + 0.9:.2f});']
    return page(duree, "\n".join(corps), "", "\n".join(script))


def trois_mineraux(duree, instants):
    mins = [("Compreignacite", "1964"), ("Rameauite", "1972"), ("Agrinierite", "1972")]
    corps = [tete("Décrits pour la première fois", "à Margnac")]
    script = [ENTREE_TETE]
    for i, ((nom, an), t) in enumerate(zip(mins, instants)):
        corps.append(f'        <div id="m{i}" style="position:absolute;top:{520 + i * 180}px;left:150px;width:780px;height:150px;'
                     'border-radius:26px;background:rgba(123,44,191,0.16);border:3px solid rgba(199,125,255,0.6);display:flex;'
                     f'align-items:center;justify-content:space-between;padding:0 40px"><span style="font-size:52px;font-weight:800">{nom}</span>'
                     f'<span class="grand" style="font-size:56px">{an}</span></div>')
        script.append(f'      tl.fromTo("#m{i}", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {t:.2f});')
    return page(duree, "\n".join(corps), "", "\n".join(script))


def champeaux(duree):
    corps = [tete("Autunois · Saône-et-Loire", "Le premier uranium"),
             '        <div id="annee" class="grand" style="position:absolute;top:560px;width:100%;text-align:center;font-size:260px">1780</div>',
             '        <div id="nom" style="position:absolute;top:860px;width:100%;text-align:center;font-size:44px;font-weight:700">Joseph-François de Champeaux</div>',
             '        <div id="legende" class="petit" style="position:absolute;top:930px;left:110px;width:860px;text-align:center">'
             'premier phosphate d\'uranium signalé en France</div>']
    script = [ENTREE_TETE, apparition("#annee", 0.3, 30), compteur("#annee", 1780, 1800, 0.4, 1.6, separateur=False),
              apparition("#nom", 1.5), apparition("#legende", 1.8)]
    return page(duree, "\n".join(corps), "", "\n".join(script))


# ---------------------------------------------------------------- fiches chimiques (photo du minéral en fond)

CSS_FICHE = """
#carte { position:absolute; top:470px; left:90px; width:900px; padding:40px 30px 36px; border-radius:34px;
  background:rgba(11,7,16,0.66); border:2px solid rgba(199,125,255,0.55); box-shadow:0 24px 60px rgba(0,0,0,0.55); }
#formule { text-align:center; font-weight:700; white-space:nowrap; }
#formule sub { font-size:0.55em; vertical-align:-0.25em; }
#fluo { margin-top:22px; text-align:center; font-size:34px; font-weight:600; color:var(--uranium); }
#elements { margin-top:30px; display:flex; justify-content:center; gap:18px; }
.el { width:150px; text-align:center; }
.rond { width:100px; height:100px; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:44px; font-weight:800; background:var(--violet); box-shadow:0 0 24px rgba(123,44,191,0.6); }
.rond.u { background:#3d5a12; border:3px solid var(--uranium); color:var(--uranium); box-shadow:0 0 26px rgba(212,242,90,0.55); }
.el-nom { margin-top:10px; font-size:27px; font-weight:600; color:var(--gris); }
#mohs { margin-top:34px; padding:0 30px; }
#mohs-titre { display:flex; justify-content:space-between; font-size:30px; font-weight:600; color:var(--gris); margin-bottom:12px; }
#mohs-titre b { color:#fff; font-weight:800; }
#graduation { position:relative; height:18px; border-radius:9px; background:rgba(255,255,255,0.14); overflow:hidden; }
#graduation-plein { position:absolute; left:0; top:0; height:100%; border-radius:9px; background:linear-gradient(90deg, var(--violet), var(--violet-clair)); transform-origin:left center; }
"""


def fiche(duree, cle, assets):
    f = FICHES[cle]
    preparer_fond(f["photo"], assets)
    els = "".join(f'<div class="el"><div class="rond{" u" if s == "U" else ""}">{s}</div><div class="el-nom">{ELEMENTS[s]}</div></div>'
                  for s in f["elements"])
    lo, hi = f["durete"]
    corps = "\n".join([
        tete("Composition", f["nom"]),
        f'        <div id="carte"><div id="formule" style="font-size:{f["taille"]}px">{f["formule"]}</div>'
        f'<div id="fluo">{f["fluo"]}</div><div id="elements">{els}</div>'
        f'<div id="mohs"><div id="mohs-titre"><span>Dureté (échelle de Mohs, 1 à 10)</span><b>{f["durete_txt"]}</b></div>'
        f'<div id="graduation"><div id="graduation-plein" style="width:{hi * 10:.0f}%"></div></div></div></div>',
    ])
    k = min(1.0, duree / 4.8)  # fiche courte : animations resserrées pour laisser le temps de lire
    script = [ENTREE_TETE,
              f'      tl.fromTo("#carte", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {0.25 * k:.2f});',
              f'      tl.fromTo("#formule", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: {0.8 * k:.2f}, ease: "power2.inOut" }}, {0.4 * k:.2f});',
              apparition("#fluo", 0.9 * k, 12, 0.35)]
    for i in range(len(f["elements"])):
        script.append(f'      tl.fromTo("#elements .el:nth-child({i + 1})", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }}, {(1.05 + 0.08 * i) * k:.2f});')
    t = (1.15 + 0.08 * len(f["elements"])) * k
    script.append(apparition("#mohs", t, 10, 0.35))
    script.append(f'      tl.fromTo("#graduation-plein", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "power2.out" }}, {t + 0.1:.2f});')
    if "U" in f["elements"]:
        script.append('      tl.fromTo(".rond.u", { boxShadow: "0 0 10px rgba(212,242,90,0.3)" }, { boxShadow: "0 0 34px rgba(212,242,90,0.85)", duration: 0.7, yoyo: true, repeat: 1, ease: "sine.inOut" }, %.2f);' % (t + 0.3))
    return page(duree, corps, CSS_FICHE, "\n".join(script), photo=True)


def ouraline(duree, t_riedel, assets):
    preparer_fond("photo_10.jpg", assets)
    corps = [tete("Verre à l'uranium", "Ouraline"),
             '        <div id="carte" style="position:absolute;top:470px;left:90px;width:900px;padding:40px 30px;border-radius:34px;'
             'background:rgba(11,7,16,0.66);border:2px solid rgba(199,125,255,0.55);text-align:center">'
             '<div class="petit">Teneur habituelle en uranium</div>'
             '<div style="margin-top:10px"><span id="bas" class="grand" style="font-size:150px">0</span>'
             '<span class="grand" style="font-size:90px"> à </span><span id="haut" class="grand" style="font-size:150px">0</span>'
             '<span class="grand" style="font-size:90px"> %</span></div></div>',
             '        <div id="dates" style="position:absolute;top:860px;left:110px;width:860px;display:flex;justify-content:space-between;gap:24px">'
             '<div id="d1" style="flex:1;text-align:center;padding:24px;border-radius:26px;background:rgba(11,7,16,0.66);border:2px solid rgba(199,125,255,0.45)">'
             '<div class="grand" style="font-size:80px">1834</div><div class="petit" style="font-size:30px;margin-top:8px">Josef Riedel</div></div>'
             '<div id="d2" style="flex:1.3;text-align:center;padding:24px;border-radius:26px;background:rgba(11,7,16,0.66);border:2px solid rgba(199,125,255,0.45)">'
             '<div class="grand" style="font-size:68px;white-space:nowrap">1880-1920</div><div class="petit" style="font-size:30px;margin-top:8px">âge d\'or</div></div></div>']
    script = [ENTREE_TETE, apparition("#carte", 0.3, 30),
              compteur("#bas", 0, 0.1, 0.5, 1.2, decimales=1), compteur("#haut", 0, 2, 0.5, 1.6),
              apparition("#d1", t_riedel), apparition("#d2", t_riedel + 1.2)]
    return page(duree, "\n".join(corps), "", "\n".join(script), photo=True)


def prudence(duree, instants, assets):
    preparer_fond("photo_12.jpg", assets, flou=True)
    trefle = ('<svg width="190" height="190" viewBox="-100 -100 200 200"><circle r="96" fill="#d4f25a"/>'
              '<circle r="14" fill="#0b0710"/>' +
              "".join(f'<path d="M0,0 L{80 * __import__("math").cos(__import__("math").radians(a - 30)):.1f},{80 * __import__("math").sin(__import__("math").radians(a - 30)):.1f} '
                      f'A80,80 0 0,1 {80 * __import__("math").cos(__import__("math").radians(a + 30)):.1f},{80 * __import__("math").sin(__import__("math").radians(a + 30)):.1f} Z" '
                      'fill="#0b0710" transform="scale(1)"/>' for a in (-90, 30, 150)) +
              '<circle r="24" fill="#d4f25a"/><circle r="14" fill="#0b0710"/></svg>')
    lignes = [("Gants pour les manipuler"), ("Rangés en boîte étanche"), ("Dans une pièce aérée")]
    corps = [tete("Prudence", "Minéraux radioactifs"),
             f'        <div id="trefle" style="position:absolute;top:470px;left:445px">{trefle}</div>']
    for i, l in enumerate(lignes):
        corps.append(f'        <div id="r{i}" style="position:absolute;top:{720 + i * 120}px;left:150px;width:780px;height:100px;border-radius:24px;'
                     'background:rgba(11,7,16,0.7);border:2px solid rgba(212,242,90,0.6);display:flex;align-items:center;padding:0 34px;'
                     f'font-size:42px;font-weight:700"><span style="color:var(--uranium);margin-right:22px">✓</span>{l}</div>')
    corps.append('        <div id="src" class="petit" style="position:absolute;top:1090px;width:100%;text-align:center;font-size:28px">Recommandations de l\'IRSN</div>')
    script = [ENTREE_TETE,
              '      tl.fromTo("#trefle", { opacity: 0, scale: 0.5, rotation: -90 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.8, ease: "back.out(1.6)" }, 0.3);']
    instants = [min(t, duree - 2.6 + 0.35 * i - 0.7) for i, t in enumerate(instants)]  # tout est lisible avant la fin
    for i, t in enumerate(instants):
        script.append(f'      tl.fromTo("#r{i}", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {t:.2f});')
    script.append(apparition("#src", min(instants[-1] + 0.5, duree - 2.2), 8, 0.4))
    return page(duree, "\n".join(corps), "", "\n".join(script), photo=True)


def preparer_fond(fichier, assets, flou=False):
    from PIL import ImageFilter
    img = Image.open(ICI / "sources" / fichier).convert("RGB")
    w, h = img.size  # recadrage 9:16 centré
    cw = min(w, h * 9 / 16)
    ch = cw * 16 / 9
    img = img.crop((int((w - cw) / 2), int((h - ch) / 2), int((w + cw) / 2), int((h + ch) / 2))).resize((1080, 1920), Image.LANCZOS)
    if flou:
        img = img.filter(ImageFilter.GaussianBlur(14))
    img.save(assets / "fond.jpg", quality=90)


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
        if nom == "cea_1945":
            html = cea_1945(d, rel(nom, "la chasse"))
        elif nom == "france_bilan":
            html = france_bilan(d)
        elif nom == "margnac_tonnage":
            html = tonnage(d, "Haute-Vienne", "Margnac", 9454, 0, "", "1953", "1995", ["11 sites", "Souterrain et ciel ouvert"])
        elif nom == "trois_mineraux":
            html = trois_mineraux(d, [rel(nom, m) for m in ("compreignacite,", "rameauite", "agrinierite.")])
        elif nom.startswith("fiche_") and nom != "fiche_ouraline":
            html = fiche(d, nom[6:], assets)
        elif nom == "champeaux_1800":
            html = champeaux(d)
        elif nom == "oudots_tonnage":
            html = tonnage(d, "Saône-et-Loire", "Les Oudots", 51.3, 1, "", "1980", "1982", ["3 mines à ciel ouvert"])
        elif nom == "margabal_tonnage":
            t = rel(nom, "De 1957")
            html = tonnage(d, "Aveyron", "Margabal", 1.5, 1, "", "1957", "1960", ["Travaux de reconnaissance"],
                           t_chiffre=t, comparaison=t + 2.6)
        elif nom == "hyverneresse_tonnage":
            html = tonnage(d, "Creuse", "Hyverneresse", 500, 0, "≈ ", "1970", "1986", ["Ciel ouvert", "Souterrain"],
                           t_chiffre=rel(nom, "De 1970"))
        elif nom == "fiche_ouraline":
            html = ouraline(d, rel(nom, "Popularisée"), assets)
        elif nom == "prudence":
            html = prudence(d, [rel(nom, m) for m in ("gants,", "boîte", "pièce")], assets)
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
