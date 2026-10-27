"""Moteur de montage 9:16 de la série : plans fixes animés, sous-titres, générique.

Utilisation : un fichier de projet (voir projets/*/montage_projet.py) décrit les plans,
puis appelle `rendre(projet)`. Les plans sont calés sur des mots du texte de voix off,
ce qui permet de refaire le montage à l'identique avec un nouvel enregistrement.
"""
import difflib
import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30

# Charte (charte/CHARTE.md)
FOND_HAUT = np.array([0x0B, 0x07, 0x10], np.float32)  # RGB
FOND_BAS = np.array([0x1A, 0x0F, 0x2A], np.float32)
VIOLET = (0x7B, 0x2C, 0xBF)
VIOLET_CLAIR = (0xC7, 0x7D, 0xFF)
POLICE_TITRE = "Montserrat:style=Bold"
POLICE_TEXTE = "Montserrat:style=Medium"
POLICE_SOUS_TITRE = "Montserrat SemiBold"
TAILLE_SOUS_TITRE = 66
LARGEUR_SOUS_TITRE = 780  # 1080 - 2 x 150 px de marge
BASE_SOUS_TITRE = 1400  # ligne de base, au-dessus des 25 % du bas

# Zone image des plans « carte » : entre les titres (haut) et les sous-titres (bas)
CARTE_CENTRE_Y = 790
CARTE_LARGEUR_MAX = 980
CARTE_HAUTEUR_MAX = 760

FONDU = 0.4  # durée des fondus enchaînés, en secondes


def _police(nom, taille):
    return ImageFont.truetype(_trouver_police(nom), taille)


def _trouver_police(nom):
    sortie = subprocess.run(["fc-match", "-f", "%{file}", nom], capture_output=True, text=True)
    return sortie.stdout.strip()


def adoucir(t):
    """Courbe d'accélération/décélération douce (smootherstep)."""
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


@dataclass
class Plan:
    image: str
    debut_sur: str  # premiers mots de la phrase qui déclenche le plan
    mode: str = "plein"  # "plein" (cadre entier) ou "carte" (image dans un cadre arrondi)
    format_carte: tuple = None  # (largeur, hauteur) imposées ; sinon format de l'image
    depart: tuple = (0.5, 0.5, 1.0)  # centre x, centre y (0-1 dans l'image), zoom
    arrivee: tuple = (0.5, 0.5, 1.08)
    titres: list = field(default_factory=list)  # (texte, début relatif 0-1, fin relative 0-1)
    hauteur_carte: int = CARTE_HAUTEUR_MAX
    coupe_franche: bool = False  # True : pas de fondu à l'entrée du plan


@dataclass
class Projet:
    nom: str
    dossier: Path
    texte_voix: Path
    audio_voix: Path  # None : vidéo muette
    mots: Path  # JSON [{t, d, w}] : horodatage des mots prononcés
    plans: list
    generique: list  # lignes ; "# Titre" pour une rubrique
    logo: Path
    mots_cles: list = field(default_factory=list)
    sortie: Path = None
    duree_generique: float = 12.0


# ---------------------------------------------------------------- sous-titres

def _normaliser(mot):
    mot = unicodedata.normalize("NFKD", mot.lower())
    mot = "".join(c for c in mot if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", mot)


def aligner_texte(texte, mots):
    """Associe chaque mot du texte écrit (ponctuation, accents exacts) à un horodatage."""
    # ponctuation isolée (« ? : ») : collée au mot voisin par une espace insécable
    jetons, ouvrant = [], ""
    for j in re.split(r"[ \t\n]+", texte):  # l'espace insécable lie (« 70 000 »)
        if j == "//":  # coupure de sous-titre imposée (vidéo muette), non affichée
            continue
        if _normaliser(j):
            jetons.append(ouvrant + j)
            ouvrant = ""
        elif j in ("«", "(") or not jetons:
            ouvrant += j + " "
        else:
            jetons[-1] += " " + j
    a = [_normaliser(j) for j in jetons]
    b = [_normaliser(m["w"]) for m in mots]
    temps = [None] * len(jetons)
    for bloc in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bloc.size):
            m = mots[bloc.b + k]
            temps[bloc.a + k] = (m["t"], m["t"] + m["d"])
    # mots non reconnus (nombres lus autrement, etc.) : interpolation entre voisins
    for i, t in enumerate(temps):
        if t is None:
            av = next((temps[j][1] for j in range(i - 1, -1, -1) if temps[j]), 0.0)
            ap = next((temps[j][0] for j in range(i + 1, len(temps)) if temps[j]), av + 0.4)
            temps[i] = (av, max(av + 0.05, ap))
    return list(zip(jetons, temps))


def _largeur(texte, police):
    return police.getlength(texte)


def decouper_sous_titres(alignes, ponctuation=True, seuil_blanc=0.6):
    """Phrases courtes, 2 lignes maximum, coupées aux frontières de sens.
    ponctuation=False (vidéo muette) : une ligne de texte = un sous-titre, sauf si trop longue."""
    # libass dimensionne la police sur sa hauteur totale : ≈ 0,727 x la taille Pillow (mesuré)
    police = _police(POLICE_SOUS_TITRE, round(TAILLE_SOUS_TITRE * 0.727))
    blocs, courant = [], []

    def tient(jetons):
        return len(_repartir_lignes([j for j, _ in jetons], police)) <= 2

    if not ponctuation:
        return _finir_sous_titres(_blocs_par_ligne(alignes, tient, seuil_blanc), police)

    for i, (jeton, t) in enumerate(alignes):
        if courant and (not tient(courant + [(jeton, t)]) or t[0] - courant[-1][1][1] > seuil_blanc):
            blocs.append(courant)
            courant = []
        courant.append((jeton, t))
        fin_phrase = re.search(r"[.?!…]»?$", jeton)
        virgule = re.search(r"[,:;]$", jeton) and len(" ".join(j for j, _ in courant)) >= 14
        if ponctuation and (fin_phrase or virgule):
            blocs.append(courant)
            courant = []
    if courant:
        blocs.append(courant)

    return _finir_sous_titres(blocs, police)


def _blocs_par_ligne(alignes, tient, seuil_blanc):
    """Une ligne de texte par bloc ; une ligne trop longue est coupée en parts équilibrées,
    de préférence après une virgule, sans laisser de mot orphelin."""
    lignes, courant = [], []
    for jeton, t in alignes:
        if courant and t[0] - courant[-1][1][1] > seuil_blanc:
            lignes.append(courant)
            courant = []
        courant.append((jeton, t))
    if courant:
        lignes.append(courant)

    def couper(bloc):
        if tient(bloc) or len(bloc) < 2:
            return [bloc]
        milieu = len(bloc) / 2
        k = min(range(1, len(bloc)), key=lambda i: abs(i - milieu) - (1.5 if re.search(r"[,:;…]$", bloc[i - 1][0]) else 0))
        return couper(bloc[:k]) + couper(bloc[k:])

    return [b for ligne in lignes for b in couper(ligne)]


def _finir_sous_titres(blocs, police):
    sous_titres = []
    for k, bloc in enumerate(blocs):
        debut, fin = bloc[0][1][0], bloc[-1][1][1] + 0.15
        if k + 1 < len(blocs):
            suivant = blocs[k + 1][0][1][0]
            fin = suivant if suivant - fin < 0.35 else fin
        fin = max(fin, debut + 0.9)
        lignes = _repartir_lignes([j for j, _ in bloc], police)
        sous_titres.append((debut, fin, lignes))
    for k in range(len(sous_titres) - 1):  # pas de chevauchement
        d, f, l = sous_titres[k]
        sous_titres[k] = (d, min(f, sous_titres[k + 1][0]), l)
    return sous_titres


def _repartir_lignes(jetons, police):
    texte = " ".join(jetons)
    if _largeur(texte, police) <= LARGEUR_SOUS_TITRE:
        return [texte]
    meilleur = None
    for k in range(1, len(jetons)):
        l1, l2 = " ".join(jetons[:k]), " ".join(jetons[k:])
        w1, w2 = _largeur(l1, police), _largeur(l2, police)
        if max(w1, w2) > LARGEUR_SOUS_TITRE:
            continue
        score = abs(w1 - w2) - (120 if re.search(r"[,:;]$", jetons[k - 1]) else 0)
        if meilleur is None or score < meilleur[0]:
            meilleur = (score, [l1, l2])
    return meilleur[1] if meilleur else [texte, "", ""]


def ecrire_ass(sous_titres, mots_cles, chemin):
    def ts(s):
        h, r = divmod(s, 3600)
        m, s = divmod(r, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    marge_v = H - BASE_SOUS_TITRE
    lignes = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Sous-titre,{POLICE_SOUS_TITRE},{TAILLE_SOUS_TITRE},&H00FFFFFF,&H00FFFFFF,&H00000000,"
        f"&H96000000,0,0,0,0,100,100,0,0,1,3.5,2,2,150,150,{marge_v},1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    # mot-clé en violet clair, à sa première apparition seulement
    cles, deja = {_normaliser(m) for m in mots_cles}, set()
    for debut, fin, texte in sous_titres:
        texte = "\\N".join(surligner(l, cles, deja) for l in texte)
        lignes.append(f"Dialogue: 0,{ts(debut)},{ts(fin)},Sous-titre,,0,0,0,,{{\\fad(80,80)}}{texte}")
    Path(chemin).write_text("\n".join(lignes) + "\n", encoding="utf-8")


def surligner(ligne, cles, deja):
    sortie = []
    for mot in ligne.split(" "):
        cle = _normaliser(mot)
        if cle in cles and cle not in deja:
            deja.add(cle)
            mot = "{\\c&H00FF7DC7&}" + mot + "{\\c}"
        sortie.append(mot)
    return " ".join(sortie)


def mots_lecture(texte, chemin, par_mot=0.36, base=0.9, mini=2.2, maxi=5.2, blanc=0.25):
    """Vidéo sans voix : horodatage fictif, une ligne de texte = un sous-titre,
    affiché le temps de le lire confortablement. « // » impose une coupure dans une ligne."""
    mots, t = [], 0.4
    for ligne in (m for l in texte.splitlines() for m in l.split("//")):
        jetons = [j for j in re.split(r"[ \t]+", ligne) if _normaliser(j)]
        if not jetons:
            continue
        duree = min(max(par_mot * len(jetons) + base, mini), maxi)
        pas = (duree - blanc) / len(jetons)
        mots += [{"t": t + k * pas, "d": pas * 0.9, "w": j} for k, j in enumerate(jetons)]
        t += duree
    Path(chemin).write_text(json.dumps(mots, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- images

def fond_degrade():
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    fond = FOND_HAUT * (1 - t) + FOND_BAS * t
    return np.repeat(fond[:, None, :], W, axis=1).reshape(H, W, 3)


VOILE_FORCE = 0.55  # assombrissement maximal derrière les sous-titres (photos claires : cartes, fonds crème)


def _voile_sous_titres():
    """Assombrissement doux derrière les sous-titres, pour les photos en plein cadre."""
    y = np.arange(H, dtype=np.float32)
    montee = np.clip((y - 1080) / 170, 0, 1)
    descente = np.clip((1600 - y) / 140, 0, 1)
    return (1 - VOILE_FORCE * adoucir_tableau(np.minimum(montee, descente)))[:, None, None]


def adoucir_tableau(t):
    return t * t * (3 - 2 * t)


VOILE_SOUS_TITRES = _voile_sous_titres()


class Rendu:
    """Prépare un plan une fois, puis produit chacune de ses images."""

    def __init__(self, plan, dossier):
        self.plan = plan
        src = Image.open(dossier / plan.image).convert("RGB")
        self.src = np.asarray(src, np.float32)
        self.h_src, self.w_src = self.src.shape[:2]
        ratio = self.w_src / self.h_src
        if plan.mode == "plein":
            self.vue = (0, 0, W, H)
            self.fond = None
        else:
            if plan.format_carte:
                wc, hc = plan.format_carte
            else:
                hc = min(plan.hauteur_carte, CARTE_LARGEUR_MAX / ratio)
                wc = hc * ratio
            x0, y0 = (W - wc) / 2, CARTE_CENTRE_Y - hc / 2
            self.vue = (int(round(x0)), int(round(y0)), int(round(wc)), int(round(hc)))
            self.fond = self._fond_carte()
            self.masque = self._masque_carte()

    def _fond_carte(self):
        """Fond uni de la charte, avec une ombre douce sous la carte."""
        x, y, w, h = self.vue
        ombre = np.zeros((H, W), np.float32)
        ombre[y + 18:y + h + 18, x:x + w] = 1
        ombre = cv2.GaussianBlur(ombre, (0, 0), 28)[..., None]
        return fond_degrade() * (1 - 0.6 * ombre)

    def _masque_carte(self):
        x, y, w, h = self.vue
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=44, fill=255)
        return np.asarray(m.resize((w, h), Image.LANCZOS), np.float32)[..., None] / 255

    def image(self, u):
        """u : avancement 0-1 dans le plan."""
        p = self.plan
        k = adoucir(u)
        cx, cy, z = (a + (b - a) * k for a, b in zip(p.depart, p.arrivee))
        x, y, w, h = self.vue
        # plus grande zone de même format que la vue, contenue dans l'image source
        if self.w_src / self.h_src > w / h:
            bh = self.h_src
            bw = bh * w / h
        else:
            bw = self.w_src
            bh = bw * h / w
        rw, rh = bw / z, bh / z
        x0 = min(max(cx * self.w_src - rw / 2, 0), self.w_src - rw)
        y0 = min(max(cy * self.h_src - rh / 2, 0), self.h_src - rh)
        s = w / rw
        M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
        interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
        vue = cv2.warpAffine(self.src, M, (w, h), flags=interp, borderMode=cv2.BORDER_REFLECT)
        if self.fond is None:
            return vue * VOILE_SOUS_TITRES
        cadre = self.fond.copy()
        zone = cadre[y:y + h, x:x + w]
        cadre[y:y + h, x:x + w] = zone * (1 - self.masque) + vue * self.masque
        return cadre


_cache_titres = {}


def titre_rgba(texte):
    """Titre à l'écran : texte blanc gras, filet violet dessous. Placé en haut, sous la zone des onglets."""
    if texte in _cache_titres:
        return _cache_titres[texte]
    police = _police(POLICE_TITRE, 56)
    calque = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    lw = police.getlength(texte)
    d.text(((W - lw) / 2 + 3, 43), texte, font=police, fill=(0, 0, 0, 150))
    d.text(((W - lw) / 2, 40), texte, font=police, fill=(255, 255, 255, 255))
    d.rounded_rectangle(((W - 120) / 2, 124, (W + 120) / 2, 132), radius=4, fill=VIOLET_CLAIR + (255,))
    calque = np.asarray(calque, np.float32) / 255
    _cache_titres[texte] = calque
    return calque


Y_TITRE = 250


def poser_titre(cadre, texte, alpha):
    # voile sombre dégradé derrière le titre, pour rester lisible sur une photo claire
    voile = np.concatenate([np.linspace(0.55, 0.55, 260), np.linspace(0.55, 0, 260)]).astype(np.float32)
    zone = cadre[Y_TITRE - 150:Y_TITRE - 150 + voile.size]
    cadre[Y_TITRE - 150:Y_TITRE - 150 + voile.size] = zone * (1 - voile[:, None, None] * alpha)
    c = titre_rgba(texte)
    a = c[..., 3:4] * alpha
    zone = cadre[Y_TITRE:Y_TITRE + c.shape[0]]
    cadre[Y_TITRE:Y_TITRE + c.shape[0]] = zone * (1 - a) + c[..., :3] * 255 * a


# ---------------------------------------------------------------- générique

def image_generique(lignes, logo_chemin):
    """Grande image du générique (texte défilant), et logo détouré en fondu."""
    p_rub = _police(POLICE_TITRE, 46)
    p_txt = _police(POLICE_TEXTE, 40)
    hauteur = H + 120 * len(lignes) + H
    toile = Image.new("RGBA", (W, hauteur), (0, 0, 0, 0))
    d = ImageDraw.Draw(toile)
    y = H
    for ligne in lignes:
        if ligne.startswith("# "):
            y += 40
            t = ligne[2:]
            d.text(((W - p_rub.getlength(t)) / 2, y), t, font=p_rub, fill=VIOLET_CLAIR)
            y += 66
            continue
        for sous in _couper(ligne, p_txt, 840):
            d.text(((W - p_txt.getlength(sous)) / 2, y), sous, font=p_txt, fill=(235, 235, 240))
            y += 54
        y += 14
    toile = toile.crop((0, 0, W, y + H // 2))

    logo = Image.open(logo_chemin).convert("RGB").resize((620, 620), Image.LANCZOS)
    masque = np.zeros((620, 620), np.float32)
    cv2.circle(masque, (310, 310), 270, 1.0, -1)
    masque = cv2.GaussianBlur(masque, (0, 0), 30)
    logo = np.dstack([np.asarray(logo, np.float32), masque * 255]) / 255
    return np.asarray(toile, np.float32) / 255, logo


def _couper(texte, police, largeur):
    mots, lignes, cour = texte.split(" "), [], ""
    for m in mots:
        essai = (cour + " " + m).strip()
        if police.getlength(essai) > largeur and cour:
            lignes.append(cour)
            cour = m
        else:
            cour = essai
    return lignes + [cour]


def cadre_generique(t, duree, toile, logo, fond):
    """Défilement du texte, puis logo seul sur les 3,5 dernières secondes."""
    cadre = fond.copy()
    duree_defil = duree - 3.5
    if t < duree_defil:
        course = toile.shape[0] - H // 2 - H
        y = int(H * 0 + course * min(t / duree_defil, 1))
        morceau = toile[y:y + H]
        a = morceau[..., 3:4]
        alpha = min(1, t / 0.6, (duree_defil - t) / 0.6)
        cadre[:morceau.shape[0]] = cadre[:morceau.shape[0]] * (1 - a * alpha) + morceau[..., :3] * 255 * a * alpha
    else:
        tl = t - duree_defil
        alpha = min(1, tl / 0.8, (3.5 - tl) / 0.6)
        x, y = (W - 620) // 2, 560
        a = logo[..., 3:4] * max(alpha, 0)
        zone = cadre[y:y + 620, x:x + 620]
        cadre[y:y + 620, x:x + 620] = zone * (1 - a) + logo[..., :3] * 255 * a
    return cadre


# ---------------------------------------------------------------- assemblage

def _horaires(projet, alignes):
    texte = [_normaliser(j) for j, _ in alignes]
    debuts, depuis = [], 0
    for plan in projet.plans:
        cible = [c for c in (_normaliser(m) for m in plan.debut_sur.split()) if c]
        for i in range(depuis, len(texte) - len(cible) + 1):
            if texte[i:i + len(cible)] == cible:
                debuts.append(max(0.0, alignes[i][1][0] - 0.12))
                depuis = i + 1
                break
        else:
            raise ValueError(f"Phrase introuvable dans le texte : {plan.debut_sur!r}")
    debuts[0] = 0.0
    fin_voix = alignes[-1][1][1]
    return debuts, fin_voix + 1.2


def rendre(projet, apercu=None):
    """apercu : liste de temps (s) -> n'enregistre que ces images en PNG."""
    sortie = projet.sortie or projet.dossier / "exports" / f"{projet.nom}.mp4"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    travail = projet.dossier / "exports" / "_travail"
    travail.mkdir(parents=True, exist_ok=True)

    mots = json.loads(Path(projet.mots).read_text())
    alignes = aligner_texte(Path(projet.texte_voix).read_text(encoding="utf-8"), mots)
    if projet.audio_voix is None:
        sous_titres = decouper_sous_titres(alignes, ponctuation=False, seuil_blanc=0.2)
    else:
        sous_titres = decouper_sous_titres(alignes)
    ass = travail / f"{projet.nom}.ass"
    ecrire_ass(sous_titres, set(projet.mots_cles), ass)

    debuts, fin_visuel = _horaires(projet, alignes)
    fins = debuts[1:] + [fin_visuel]
    duree_totale = fin_visuel + projet.duree_generique
    rendus = [Rendu(p, projet.dossier / "sources") for p in projet.plans]
    toile, logo = image_generique(projet.generique, projet.dossier / "sources" / projet.logo)
    fond = fond_degrade()

    def cadre_a(t):
        if t >= fin_visuel:
            return cadre_generique(t - fin_visuel, projet.duree_generique, toile, logo, fond)
        cadre = None
        for i, (r, d, f) in enumerate(zip(rendus, debuts, fins)):
            entree = 0 if (i == 0 or r.plan.coupe_franche) else FONDU / 2
            sortie_ = FONDU / 2 if i + 1 < len(rendus) and not rendus[i + 1].plan.coupe_franche else 0
            if not (d - entree <= t < f + sortie_):
                continue
            u = (t - (d - entree)) / ((f + sortie_) - (d - entree))
            img = r.image(u)
            for texte, a, b in r.plan.titres:
                ta, tb = d + a * (f - d), d + b * (f - d)
                if ta <= t <= tb:
                    poser_titre(img, texte, min(1, (t - ta) / 0.3, (tb - t) / 0.3))
            if cadre is None:
                cadre = img
            else:  # fondu enchaîné avec le plan précédent
                alpha = adoucir((t - (d - entree)) / FONDU)
                cadre = cadre * (1 - alpha) + img * alpha
        if t > fin_visuel - 0.6:  # fondu au noir avant le générique
            cadre = cadre * max(0, (fin_visuel - t) / 0.6)
        return cadre

    if apercu:
        chemins = []
        for t in apercu:
            img = np.clip(cadre_a(t), 0, 255).astype(np.uint8)
            chemin = travail / f"apercu_{t:06.2f}.png"
            Image.fromarray(img).save(chemin)
            chemins.append(chemin)
        return chemins, ass

    n = int(round(duree_totale * FPS))
    video_brute = travail / f"{projet.nom}_image.mp4"
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-vf", f"subtitles={ass}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(video_brute)], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(np.clip(cadre_a(i / FPS), 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("Échec de l'encodage vidéo")

    if projet.audio_voix is None:  # vidéo muette : piste son silencieuse, pour la compatibilité des plateformes
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(video_brute),
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-t", f"{duree_totale:.3f}", "-movflags", "+faststart", str(sortie)], check=True)
        return sortie

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video_brute), "-i", str(projet.audio_voix),
        "-filter_complex",
        f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,afade=t=out:st={fin_visuel - 0.6:.2f}:d=0.6,"
        f"apad=whole_dur={duree_totale:.3f}[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{duree_totale:.3f}", "-movflags", "+faststart", str(sortie)], check=True)
    return sortie
