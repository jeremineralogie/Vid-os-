"""Assemblage final : plans Blender + fondus, étalonnage, titres et sous-titres (ASS), logo, mixage audio, export.

python3 assembler.py            -> exports/JEREMINERALOGIE_CE_QUE_TU_NE_VOIS_PAS.mp4
python3 assembler.py apercu 2,30,63.9  -> exports/apercus/*.png (images du montage final)
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ICI = Path(__file__).resolve().parent
RENDU = ICI / "sources/rendu"
TRAVAIL = ICI / "exports/_travail"
SORTIE = ICI / "exports/JEREMINERALOGIE_CE_QUE_TU_NE_VOIS_PAS.mp4"
DUREE = 65.0

# début de chaque paragraphe de la voix off (s), calé sur les séquences du découpage
VOIX = [0.35, 6.3, 12.4, 22.6, 35.4, 48.4, 56.4]

# plans : (préfixe, première image, dernière image) — temps global t = (image - 1) / 30
PLANS = [("ext", 1, 226), ("int", 205, 1755), ("ext", 1715, 1950)]
FONDUS = [(6.8, 0.7), (57.133, 1.333)]  # (début, durée) : A->B puis B->C

MOTS_CLES = {"fluides", "fluorure", "calcium", "fluorite", "cristaux", "zonations", "fractures", "archive"}

# titres : (début, fin, texte, style)
TITRES = [
    (2.0, 5.3, r"TU PASSERAIS DEVANT\NSANS MÊME LE REGARDER…", "Accroche"),
    (7.6, 11.9, "UNE FRACTURE DANS LA ROCHE", "Titre"),
    (13.4, 21.6, r"DES FLUIDES RICHES\NEN ÉLÉMENTS DISSOUS", "Titre"),
    (24.0, 29.6, "CaF₂ — FLUORURE DE CALCIUM", "Titre"),
    (24.6, 33.6, r"{\c&HF0E6E6&}●{\c&HFFFFFF&} Ca²⁺     {\c&HEF9AB4&}●{\c&HFFFFFF&} F⁻", "Legende"),
    (30.2, 34.9, "LA CRISTALLISATION COMMENCE", "Titre"),
    (37.0, 47.2, "UNE STRUCTURE CRISTALLINE CUBIQUE", "Titre"),
    (49.4, 56.4, r"PLUSIEURS MILLIONS D’ANNÉES\ND’HISTOIRE GÉOLOGIQUE", "Titre"),
    (7.2, 23.0, "RECONSTITUTION 3D", "Mention"),
    (23.0, 48.0, "RECONSTITUTION 3D · TEMPS ACCÉLÉRÉ", "Mention"),
    (48.0, 57.0, "RECONSTITUTION 3D", "Mention"),
    (60.5, 65.0, "jeremineralogie.fr", "Site"),
    (62.0, 65.0, r"LA GÉOLOGIE EST PARTOUT.\NIL SUFFIT DE SAVOIR REGARDER.", "Final"),
    (63.8, 65.0, r"ABONNE-TOI POUR DÉCOUVRIR\NLES SECRETS DES MINÉRAUX", "Appel"),
]

ENTETE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SousTitre,Montserrat SemiBold,66,&H00FFFFFF,&H00A0A0A0,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,4.5,0,2,110,110,500,1
Style: Accroche,Montserrat SemiBold,62,&H00F0E6E6,&H00F0E6E6,&H000C0808,&H00000000,0,0,0,0,100,100,3,0,1,0,0,8,110,110,330,1
Style: Titre,Montserrat Medium,52,&H00F0E6E6,&H00F0E6E6,&H000C0808,&H00000000,0,0,0,0,100,100,5,0,1,0,0,8,110,110,320,1
Style: Legende,Montserrat Medium,42,&H00F0E6E6,&H00F0E6E6,&H000C0808,&H00000000,0,0,0,0,100,100,2,0,1,0,0,8,110,110,410,1
Style: Mention,Montserrat Medium,28,&H40EF9AB4,&H40EF9AB4,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,8,110,110,255,1
Style: Site,Montserrat Medium,34,&H00FF7DC7,&H00FF7DC7,&H000C0808,&H00000000,0,0,0,0,100,100,2,0,1,0,0,8,110,110,600,1
Style: Final,Montserrat SemiBold,50,&H00F0E6E6,&H00F0E6E6,&H000C0808,&H00000000,0,0,0,0,100,100,3,0,1,0,0,8,90,90,1170,1
Style: Appel,Montserrat Medium,34,&H00EF9AB4,&H00EF9AB4,&H000C0808,&H00000000,0,0,0,0,100,100,3,0,1,0,0,8,110,110,1340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ombre(style):
    """Ombre douce derrière les titres (copie floutée sombre, couche 0)."""
    return r"{\bord6\blur10\3c&H0C0808&\3a&H40&\1a&HFF&}" if style != "Mention" else None


def evenements_titres():
    lignes = []
    for t0, t1, texte, style in TITRES:
        fin_film = t1 >= DUREE
        fad = r"{\fad(%d,%d)}" % (500 if style != "Accroche" else 700, 0 if fin_film else 450)
        # léger glissement vers le haut à l'apparition
        if style in ("Titre", "Accroche", "Final"):
            fad += r"{\fscx100\fscy100\t(0,600,\fsp%s)}" % ("5" if style == "Titre" else "3")
        o = ombre(style)
        if o:
            lignes.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{fad}{o}{texte}")
        lignes.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{fad}{texte}")
        if style == "Titre":  # filet violet sous le titre
            y = 320 + (2 * 66 if r"\N" in texte else 66) + 14
            lignes.append(f"Dialogue: 1,{ts(t0 + 0.25)},{ts(t1)},Titre,,0,0,0,,"
                          r"{\fad(500,450)\an7\pos(500,%d)\1c&HC95076&\p1\t(0,700,\fscx100)}m 0 0 l 80 0 80 3 0 3{\p0}" % y)
    return lignes


def propre(m):
    return m.strip(" ,.;:!?…«»\"'’").lower()


PARAGRAPHES = [p.strip() for p in (ICI / "voix_off.txt").read_text(encoding="utf-8").split("\n\n") if p.strip()]


def _norm(w):
    return "".join(c for c in w.lower() if c.isalnum())


def realigner(mots, texte):
    """Remplace les mots de la synthèse (sans ponctuation) par ceux du texte, en gardant les horodatages."""
    sortie, k = [], 0
    for jeton in texte.split():
        cible = _norm(jeton)
        if not cible:  # ponctuation isolée (« — »)
            if sortie:
                sortie[-1]["w"] += " " + jeton
            continue
        debut, acc = k, ""
        while k < len(mots) and len(acc) < len(cible):
            acc += _norm(mots[k]["w"])
            k += 1
        a, b = mots[debut], mots[max(k - 1, debut)]
        sortie.append({"t": a["t"], "d": b["t"] + b["d"] - a["t"], "w": jeton})
    return sortie


def evenements_sous_titres():
    """Karaoké : chaque mot passe du gris au blanc ; mots-clés en violet clair à leur première apparition."""
    lignes, vus = [], set()
    for i, debut in enumerate(VOIX):
        mots = json.loads((ICI / f"audio/seg_{i + 1}.json").read_text(encoding="utf-8"))
        mots = [dict(m, t=m["t"] + debut) for m in mots]
        mots = realigner(mots, PARAGRAPHES[i])
        # le texte de l'accroche est déjà à l'écran : pas de sous-titre pour la première phrase
        if i == 0:
            k = next(j for j, m in enumerate(mots) if m["w"].startswith("Et"))
            mots = mots[k:]
        # découpage en cartons de 2 lignes (≈ 26 caractères par ligne), coupés aux ponctuations
        cartons, courant = [], []
        for m in mots:
            courant.append(m)
            longueur = sum(len(x["w"]) + 1 for x in courant)
            if courant and len(courant) > 1 and longueur > 44 and len(propre(courant[-1]["w"])) <= 3:
                dernier = courant.pop()
                cartons.append(courant)
                courant = [dernier]
                continue
            if longueur > 44 or (m["w"][-1] in ".?!" and longueur > 12) or (m["w"][-1] == "," and longueur > 30):
                cartons.append(courant)
                courant = []
        if courant:
            cartons.append(courant)
        for j, c in enumerate(cartons):
            t0 = c[0]["t"] - 0.08
            fin_c = c[-1]["t"] + c[-1]["d"]
            t1 = cartons[j + 1][0]["t"] - 0.1 if j + 1 < len(cartons) else fin_c + 0.5
            t1 = min(t1, fin_c + 0.9)
            # retour à la ligne équilibré
            txt = [m["w"] for m in c]
            total = sum(len(w) + 1 for w in txt)
            coupe, acc = len(txt), 0
            if total > 24:
                for k, w in enumerate(txt):
                    acc += len(w) + 1
                    if acc >= total / 2:
                        coupe = k + 1
                        break
            morceaux = []
            for k, m in enumerate(c):
                dur = (c[k + 1]["t"] - m["t"]) if k + 1 < len(c) else m["d"]
                cle = propre(m["w"])
                mot = m["w"]
                if cle in MOTS_CLES and cle not in vus:
                    vus.add(cle)
                    mot = r"{\1c&HFF7DC7&}" + mot + r"{\1c&HFFFFFF&}"
                sep = r"\N" if k == coupe and k < len(c) else (" " if k else "")
                morceaux.append(sep + r"{\kf%d}" % max(int(dur * 100), 1) + mot)
            avance = int((c[0]["t"] - t0) * 100)
            lignes.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},SousTitre,,0,0,0,,{{\\fad(120,120)}}{{\\k{avance}}}" + "".join(morceaux))
    return lignes


def ecrire_ass():
    TRAVAIL.mkdir(parents=True, exist_ok=True)
    chemin = TRAVAIL / "textes.ass"
    chemin.write_text(ENTETE + "\n".join(evenements_titres() + evenements_sous_titres()) + "\n", encoding="utf-8")
    return chemin


def logo_cercle(taille=300):
    """Logo officiel, sans modification, détouré en cercle avec bord fondu (charte)."""
    im = Image.open(ICI / "sources/LOGO_jeremineralogie.jpg").convert("RGB").resize((taille, taille), Image.LANCZOS)
    y, x = np.mgrid[:taille, :taille]
    r = np.hypot(x - taille / 2, y - taille / 2) / (taille / 2)
    a = np.clip((1 - r) / 0.12, 0, 1)
    rgba = np.dstack([np.asarray(im), (a * 255).astype(np.uint8)])
    chemin = TRAVAIL / "logo.png"
    Image.fromarray(rgba, "RGBA").save(chemin)
    return chemin


def filtre_video(ass, logo_y=262):
    f = []
    for k, (pref, a, b) in enumerate(PLANS):
        f.append(f"[{k}:v]trim=end_frame={b - a + 1},setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,format=yuv444p,fps=30[p{k}]")
    (o1, d1), (o2, d2) = FONDUS
    f.append(f"[p0][p1]xfade=transition=fade:duration={d1}:offset={o1}[ab]")
    f.append(f"[ab][p2]xfade=transition=fade:duration={d2}:offset={o2}[abc]")
    # étalonnage : légère courbe, vignettage, grain fin (texture « cinéma »)
    f.append("[abc]eq=contrast=1.04:saturation=1.05,vignette=angle=PI/5:mode=forward,"
             "noise=c0s=5:c0f=t+u,unsharp=5:5:0.35,format=yuv420p[g]")
    f.append(f"[g]subtitles='{ass}':fontsdir=/usr/share/fonts/opentype/montserrat[s]")
    f.append("[3:v]format=rgba,fade=in:st=60:d=0.9:alpha=1[logo]")
    f.append(f"[s][logo]overlay=x=(W-w)/2:y={logo_y}:enable='gte(t,60)':shortest=0,"
             f"trim=duration={DUREE},format=yuv420p[v]")
    return ";".join(f)


def filtre_audio():
    n = 4  # entrées audio à partir de l'indice 4
    f = []
    for i, d in enumerate(VOIX):
        f.append(f"[{n + i}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={int(d * 1000)}:all=1[v{i}]")
    f.append("".join(f"[v{i}]" for i in range(len(VOIX))) + f"amix=inputs={len(VOIX)}:normalize=0,apad,atrim=0:{DUREE},"
             "loudnorm=I=-16:TP=-2:LRA=7,asplit=2[voix][cle]")
    k = n + len(VOIX)
    f.append(f"[{k}:a]volume=0.62[mus]")
    f.append(f"[{k + 1}:a]volume=0.75[sfx]")
    f.append("[mus][sfx]amix=inputs=2:normalize=0[fond]")
    # la musique s'efface sous la voix (compression déclenchée par la voix)
    f.append("[fond][cle]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=450:makeup=1[fond_d]")
    f.append(f"[voix][fond_d]amix=inputs=2:normalize=0:weights=1 0.55,atrim=0:{DUREE},"
             f"loudnorm=I=-14:TP=-1.5:LRA=9,aformat=sample_rates=48000[a]")
    return ";".join(f)


def entrees(logo):
    e = []
    for pref, a, b in PLANS:
        e += ["-framerate", "30", "-start_number", str(a), "-i", str(RENDU / f"{pref}_%04d.png")]
    e += ["-loop", "1", "-framerate", "30", "-i", str(logo)]
    for i in range(len(VOIX)):
        e += ["-i", str(ICI / f"audio/seg_{i + 1}.wav")]
    e += ["-i", str(ICI / "audio/musique.wav"), "-i", str(ICI / "audio/effets.wav")]
    return e


def principal():
    ass = ecrire_ass()
    logo = logo_cercle()
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y"] + entrees(logo) + [
        "-filter_complex", filtre_video(ass) + ";" + filtre_audio(),
        "-map", "[v]", "-map", "[a]", "-t", str(DUREE),
        "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-b:v", "18M", "-maxrate", "25M", "-bufsize", "36M",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", str(SORTIE)]
    if len(sys.argv) > 2 and sys.argv[1] == "apercu":
        d = ICI / "exports/apercus"
        d.mkdir(parents=True, exist_ok=True)
        for t in sys.argv[2].split(","):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", str(SORTIE), "-frames:v", "1",
                            str(d / f"final_{float(t):05.1f}.png")], check=True)
        return
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)
    print(SORTIE)


if __name__ == "__main__":
    principal()
