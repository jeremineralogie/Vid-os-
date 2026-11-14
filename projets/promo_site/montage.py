"""Vidéo promotionnelle de jeremineralogie.fr (23 s, 1080 x 1920, 30 i/s).

Uniquement des éléments réels du site : captures des pages (téléphone, 1 080 px de large), photos publiées
(fluorite d'Ussel, quartz d'Échassières), logo officiel. Pas de titres à l'écran (demande de l'auteur) :
seulement les sous-titres de la voix, puis le logo et l'adresse du site.

python3 montage.py                 -> exports/PROMO_JEREMINERALOGIE.mp4
python3 montage.py apercu 1,8,15   -> exports/apercus/*.png
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None
ICI = Path(__file__).resolve().parent
SRC = ICI / "sources"
CAP = SRC / "captures"
SORTIE = ICI / "exports/PROMO_JEREMINERALOGIE.mp4"
W, H, FPS, DUREE = 1080, 1920, 30, 23.0
NB = int(DUREE * FPS)


def charger(chemin, hauteur_max=None):
    im = Image.open(chemin).convert("RGB")
    if hauteur_max and im.height > hauteur_max:
        im = im.crop((0, 0, im.width, hauteur_max))
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR).astype(np.float32)


IMAGES = {
    "fluo": charger(SRC / "fluorite_ussel.jpg"),
    "accueil": charger(CAP / "accueil.png", 6000),
    "collection": charger(CAP / "collection.png", 6000),
    "fiche_fluo": charger(CAP / "specimen_fluorite.png", 7000),
    "boutique": charger(CAP / "boutique.png", 7000),
    "fiche_quartz": charger(CAP / "piece_quartz.png", 7000),
}


def lisse(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (6 * u - 15) + 10)  # smootherstep


def sortie_douce(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def seg(t, cles, f=lisse):
    """cles : [(t, valeur)] ; interpolation douce entre clés successives (valeurs scalaires ou tuples)."""
    if t <= cles[0][0]:
        return cles[0][1]
    for (t0, a), (t1, b) in zip(cles, cles[1:]):
        if t <= t1:
            u = f((t - t0) / (t1 - t0))
            if isinstance(a, tuple):
                return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return cles[-1][1]


def vue(nom, cx, cy, zoom):
    """Fenêtre 1080 x 1920 centrée sur (cx, cy) de l'image source, agrandie de `zoom`."""
    src = IMAGES[nom]
    M = np.float32([[zoom, 0, W / 2 - zoom * cx], [0, zoom, H / 2 - zoom * cy]])
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LANCZOS4 if zoom > 1.05 else cv2.INTER_AREA,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(16, 7, 11))


# ---------------------------------------------------------------- plans (temps global en secondes)
# coordonnées en pixels des captures (CSS x 3) : carte fluorite (43, 2117, 464 x 705) ; photo de la fiche
# fluorite (46, 1484, 988 x 741) ; carte quartz (43, 3698, 464 x 763) ; photo de la fiche quartz (46, 1685, 988 x 741)

def plan_ouverture(t):
    z = seg(t, [(0.0, 1.75), (2.5, 1.0), (3.4, 0.97)], sortie_douce)
    c = seg(t, [(0.0, (640.0, 760.0)), (2.5, (720.0, 960.0))], sortie_douce)
    return vue("fluo", c[0], c[1], z)


# Les pages du site s'affichent dans un cadre arrondi en haut de l'écran : les sous-titres (vers 1 400 px)
# tombent sous le cadre, sur un fond flouté, et ne recouvrent jamais le texte des pages.
CX0, CY0, CW, CH = 90, 150, 900, 1020
BASE = CW / 1080  # une page de 1 080 px de large tient dans le cadre
RAYON = 42
_yy, _xx = np.mgrid[:CH, :CW]
_d = np.maximum(np.maximum(RAYON - _xx, _xx - (CW - 1 - RAYON)), 0) ** 2 + \
    np.maximum(np.maximum(RAYON - _yy, _yy - (CH - 1 - RAYON)), 0) ** 2
MASQUE = np.clip(RAYON + 0.5 - np.sqrt(_d), 0, 1)[..., None].astype(np.float32)


def page(nom, cx, cy, zoom=1.0):
    """Contenu du cadre : fenêtre CW x CH centrée sur (cx, cy) de la capture, zoom 1 = pleine largeur."""
    z = zoom * BASE
    M = np.float32([[z, 0, CW / 2 - z * cx], [0, z, CH / 2 - z * cy]])
    return cv2.warpAffine(IMAGES[nom], M, (CW, CH), flags=cv2.INTER_LANCZOS4 if z > 1.05 else cv2.INTER_AREA,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(16, 7, 11))


def cadre(contenu):
    """Pose le contenu dans le cadre arrondi, sur un fond flouté et assombri de ce même contenu."""
    petit = cv2.resize(contenu, (CW // 12, CH // 12), interpolation=cv2.INTER_AREA)
    fond = cv2.GaussianBlur(cv2.resize(petit, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 25) * 0.42
    ombre = np.zeros((H, W), np.float32)
    ombre[CY0 + 18:CY0 + CH + 18, CX0:CX0 + CW] = 1
    ombre = cv2.GaussianBlur(ombre, (0, 0), 30)[..., None] * 0.55
    img = fond * (1 - ombre)
    zone = img[CY0:CY0 + CH, CX0:CX0 + CW]
    img[CY0:CY0 + CH, CX0:CX0 + CW] = zone * (1 - MASQUE) + contenu * MASQUE
    # liseré violet (charte #7B2CBF), très fin
    bord = cv2.dilate((MASQUE[..., 0] > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) - \
        (MASQUE[..., 0] > 0.5).astype(np.uint8)
    zb = img[CY0:CY0 + CH, CX0:CX0 + CW]
    a = bord[..., None].astype(np.float32) * 0.8
    img[CY0:CY0 + CH, CX0:CX0 + CW] = zb * (1 - a) + np.float32([191, 44, 123]) * a
    return img


# photos dans les cartes : fluorite (161-388, 2189-2475) ; quartz (149-402, 3825-4148).
# Sur les fiches, la photo fait 741 px de haut : zoom carte 741/286 = 2,59 et 741/323 = 2,29
# donnent la même taille que la fiche au zoom 1, d'où un fondu sans dédoublement.

def c_accueil(t):
    return page("accueil", 540, seg(t, [(2.9, 612.0), (3.7, 640.0), (6.2, 1700.0)]))


def c_collection(t):
    cy = seg(t, [(5.9, 1300.0), (7.0, 1320.0), (8.4, 2332.0)])
    u = (8.4, 9.55)
    z = seg(t, [(u[0], 1.0), (u[1], 741 / 286)])
    cx = seg(t, [(u[0], 540.0), (u[1], 274.5)])
    return page("collection", cx, cy, z)


def c_fiche_fluo(t):
    return page("fiche_fluo", 540, seg(t, [(9.4, 1855.0), (9.95, 1860.0), (12.4, 4800.0)]))


def c_boutique(t):
    cy = seg(t, [(12.3, 1300.0), (13.6, 1320.0), (14.9, 3986.5)])
    u = (14.9, 15.85)
    z = seg(t, [(u[0], 1.0), (u[1], 741 / 323)])
    cx = seg(t, [(u[0], 540.0), (u[1], 275.5)])
    return page("boutique", cx, cy, z)


def c_fiche_quartz(t):
    return page("fiche_quartz", 540, seg(t, [(15.7, 2055.0), (16.25, 2060.0), (18.7, 4300.0)]))


def glisse_c(fa, fb, t, t0, duree):
    """Glissé vers le haut à l'intérieur du cadre, avec flou de mouvement vertical."""
    u = lisse((t - t0) / duree)
    dec = int(u * CH)
    a, b = fa(t), fb(t)
    img = np.empty_like(a)
    img[:CH - dec] = a[dec:]
    img[CH - dec:] = b[:dec]
    k = int(1 + 110 * np.sin(np.pi * u))
    return cv2.blur(img, (1, k)) if k > 2 else img


def fondu_c(fa, fb, t, t0, duree):
    u = lisse((t - t0) / duree)
    return fa(t) * (1 - u) + fb(t) * u


def contenu_site(t):
    if t < 5.9:
        return c_accueil(t)
    if t < 6.35:
        return glisse_c(c_accueil, c_collection, t, 5.9, 0.45)
    if t < 9.45:
        return c_collection(t)
    if t < 9.8:
        return fondu_c(c_collection, c_fiche_fluo, t, 9.45, 0.35)
    if t < 12.3:
        return c_fiche_fluo(t)
    if t < 12.75:
        return glisse_c(c_fiche_fluo, c_boutique, t, 12.3, 0.45)
    if t < 15.75:
        return c_boutique(t)
    if t < 16.1:
        return fondu_c(c_boutique, c_fiche_quartz, t, 15.75, 0.35)
    return c_fiche_quartz(t)


def plan_site(t):
    return cadre(contenu_site(t))


FOND_FIN = None
LOGO = None
SITE = None


def preparer_fin():
    global FOND_FIN, LOGO, SITE
    im = Image.open(SRC / "fluorite_ussel.jpg").convert("RGB").resize((1440, 1920), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(28))
    fond = np.asarray(im, np.float32)[:, ::-1] * 0.32  # assombri
    FOND_FIN = cv2.cvtColor(fond.astype(np.float32), cv2.COLOR_RGB2BGR)
    taille = 560
    lg = Image.open(SRC / "LOGO_jeremineralogie.jpg").convert("RGB").resize((taille, taille), Image.LANCZOS)
    y, x = np.mgrid[:taille, :taille]
    r = np.hypot(x - taille / 2, y - taille / 2) / (taille / 2)
    a = np.clip((1 - r) / 0.12, 0, 1)
    LOGO = (cv2.cvtColor(np.asarray(lg, np.float32), cv2.COLOR_RGB2BGR), a[..., None].astype(np.float32))
    toile = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(toile)
    police = ImageFont.truetype("/usr/share/fonts/opentype/montserrat/Montserrat-SemiBold.otf", 60)
    texte = "jeremineralogie.fr"
    lg_t = d.textlength(texte, font=police)
    d.text(((W - lg_t) / 2, 20), texte, font=police, fill=(199, 125, 255, 255))
    arr = np.asarray(toile, np.float32)
    SITE = (cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2BGR), arr[..., 3:4] / 255)


def plan_fin(t):
    if FOND_FIN is None:
        preparer_fin()
    z = seg(t, [(18.8, 1.08), (23.0, 1.0)], lambda u: u)
    img = cv2.warpAffine(FOND_FIN, np.float32([[z, 0, W / 2 - z * 720], [0, z, H / 2 - z * 960]]), (W, H),
                         flags=cv2.INTER_LINEAR)
    # logo : fondu et léger grossissement
    a = lisse((t - 19.3) / 0.9)
    s = 0.9 + 0.1 * sortie_douce((t - 19.3) / 1.4)
    rgb, alpha = LOGO
    taille = int(560 * s)
    rgb_s = cv2.resize(rgb, (taille, taille), interpolation=cv2.INTER_AREA)
    al_s = cv2.resize(alpha, (taille, taille), interpolation=cv2.INTER_AREA)[..., None] * a
    x0, y0 = (W - taille) // 2, 780 - taille // 2
    zone = img[y0:y0 + taille, x0:x0 + taille]
    img[y0:y0 + taille, x0:x0 + taille] = zone * (1 - al_s) + rgb_s * al_s
    b = lisse((t - 19.9) / 0.8)
    rgb, alpha = SITE
    y1 = 1110 + int(18 * (1 - b))
    zone = img[y1:y1 + 120]
    img[y1:y1 + 120] = zone * (1 - alpha * b) + rgb * alpha * b
    return img


# ---------------------------------------------------------------- enchaînements
def glisse(f_sortant, f_entrant, t, t0, duree):
    """Transition « glissé » vers le haut, avec flou de mouvement (fouet vertical)."""
    u = lisse((t - t0) / duree)
    dec = int(u * H)
    a, b = f_sortant(t), f_entrant(t)
    img = np.empty_like(a)
    img[:H - dec] = a[dec:]
    img[H - dec:] = b[:dec]
    vitesse = np.sin(np.pi * u)  # flou maximal au milieu
    k = int(1 + 120 * vitesse)
    if k > 2:
        img = cv2.blur(img, (1, k))
    return img


def fondu(f_a, f_b, t, t0, duree):
    u = lisse((t - t0) / duree)
    return f_a(t) * (1 - u) + f_b(t) * u


def image(t):
    if t < 2.85:
        return plan_ouverture(t)
    if t < 3.4:
        return glisse(plan_ouverture, plan_site, t, 2.85, 0.55)
    if t < 18.85:
        return plan_site(t)
    if t < 19.55:
        return fondu(plan_site, plan_fin, t, 18.85, 0.7)
    return plan_fin(t)


# voile sombre sous les sous-titres (lisibilité sur les pages du site)
_y = np.arange(H, dtype=np.float32)
VOILE = (1 - 0.5 * np.exp(-((_y - 1360) / 190) ** 2))[:, None, None]


def rendre_image(f):
    t = f / FPS
    img = image(t)
    if t < 3.0:
        img = img * VOILE
    return np.clip(img, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sous-titres karaoké (charte de la série)
ENTETE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: S,Montserrat SemiBold,66,&H00FFFFFF,&H00A0A0A0,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,4.5,0,2,110,110,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
CLES = {"collectionneur", "collection", "boutique"}


def ts(t):
    return f"0:{int(t // 60):02d}:{t % 60:05.2f}"


def norm(w):
    return "".join(c for c in w.lower() if c.isalnum())


def sous_titres():
    mots = json.loads((ICI / "audio/voix.json").read_text(encoding="utf-8"))
    jetons = (ICI / "voix_off.txt").read_text(encoding="utf-8").split()
    # remettre la ponctuation du texte sur les mots horodatés
    alignes, k = [], 0
    for j in jetons:
        c = norm(j)
        if not c:
            if alignes:
                alignes[-1]["w"] += " " + j
            continue
        d, acc = k, ""
        while k < len(mots) and len(acc) < len(c):
            acc += norm(mots[k]["w"])
            k += 1
        a, b = mots[d], mots[max(k - 1, d)]
        alignes.append({"t": a["t"], "d": b["t"] + b["d"] - a["t"], "w": j})
    alignes = [m for m in alignes if m["t"] < 19.0]  # l'adresse finale est écrite sous le logo
    cartons, cur = [], []
    for m in alignes:
        cur.append(m)
        n = sum(len(x["w"]) + 1 for x in cur)
        if n > 40 or (m["w"][-1] in ".?!:" and n > 8) or (m["w"][-1] == "," and n > 26):
            cartons.append(cur)
            cur = []
    if cur:
        cartons.append(cur)
    lignes, vus = [], set()
    for i, c in enumerate(cartons):
        t0 = c[0]["t"] - 0.08
        fin = c[-1]["t"] + c[-1]["d"]
        t1 = min(cartons[i + 1][0]["t"] - 0.08 if i + 1 < len(cartons) else fin + 0.5, fin + 0.8)
        total = sum(len(m["w"]) + 1 for m in c)
        coupe, acc = len(c), 0
        if total > 22:
            for k2, m in enumerate(c):
                acc += len(m["w"]) + 1
                if acc >= total / 2:
                    coupe = k2 + 1
                    break
        morceaux = []
        for k2, m in enumerate(c):
            dur = (c[k2 + 1]["t"] - m["t"]) if k2 + 1 < len(c) else m["d"]
            mot = m["w"]
            cle = norm(mot)
            if cle in CLES and cle not in vus:
                vus.add(cle)
                mot = r"{\1c&HFF7DC7&}" + mot + r"{\1c&HFFFFFF&}"
            sep = r"\N" if k2 == coupe else (" " if k2 else "")
            morceaux.append(sep + r"{\kf%d}" % max(int(dur * 100), 1) + mot)
        lignes.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},S,,0,0,0,,{{\\fad(100,120)}}{{\\k{int((c[0]['t'] - t0) * 100)}}}"
                      + "".join(morceaux))
    chemin = ICI / "exports/_travail/sous_titres.ass"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(ENTETE + "\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


def principal():
    ass = sous_titres()
    if len(sys.argv) > 2 and sys.argv[1] == "apercu":
        d = ICI / "exports/apercus"
        d.mkdir(parents=True, exist_ok=True)
        for t in (float(x) for x in sys.argv[2].split(",")):
            brut = d / "_brut.png"
            cv2.imwrite(str(brut), rendre_image(int(round(t * FPS))))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-vf",
                            f"setpts=PTS+{t}/TB,subtitles='{ass}':fontsdir=/usr/share/fonts/opentype/montserrat",
                            str(d / f"promo_{t:04.1f}.png")], check=True)
            brut.unlink()
        return
    muet = ICI / "exports/_travail/video_muette.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-vf",
                           f"subtitles='{ass}':fontsdir=/usr/share/fonts/opentype/montserrat,format=yuv420p",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "15", str(muet)], stdin=subprocess.PIPE)
    for f in range(NB):
        ff.stdin.write(rendre_image(f).tobytes())
        if f % 60 == 0:
            print(f"{f / FPS:5.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()
    # mixage : musique abaissée sous la voix, puis export de livraison
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(muet), "-i", str(ICI / "audio/voix.wav"),
        "-i", str(ICI / "audio/musique.wav"),
        "-filter_complex",
        "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:23,loudnorm=I=-16:TP=-2,asplit[v][c];"
        "[2:a]volume=0.8[m];[m][c]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=400[md];"
        "[v][md]amix=inputs=2:normalize=0:weights=1 0.6,atrim=0:23,loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-b:v", "16M", "-maxrate", "22M",
        "-bufsize", "32M", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", "23", str(SORTIE)],
        check=True)
    print(SORTIE)


if __name__ == "__main__":
    principal()
