"""Musique originale et habillage sonore, synthétisés (aucun échantillon externe). 65 s, 48 kHz, stéréo.

python3 musique.py -> audio/musique.wav, audio/effets.wav

Structure (prompt) : 0-12 mystère grave ; 12-25 textures et montée ; 25-40 montée (cristallisation) ;
40-57 apogée (cristaux) ; 57-65 résolution. Ré mineur éolien, résolution sur ré (quinte à vide puis tierce majeure).
"""
import subprocess
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
SR = 48000
DUREE = 65.0
N = int(SR * DUREE)
T = np.arange(N) / SR
rng = np.random.default_rng(65)


def hz(note):
    """'D2', 'F#4' -> fréquence."""
    noms = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    n = noms[note[0]] + (1 if "#" in note else -1 if note[1] == "b" else 0)
    octave = int(note[-1])
    return 440.0 * 2 ** ((n + 12 * (octave - 4)) / 12)


def env(points):
    """Enveloppe linéaire par morceaux [(t, valeur)] sur toute la durée."""
    ts, vs = zip(*points)
    return np.interp(T, ts, vs)




def passe_bas_fft(x, fc, ordre=2):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    h = 1 / np.sqrt(1 + (f / fc) ** (2 * ordre))
    return np.fft.irfft(X * (h[:, None] if x.ndim > 1 else h), x.shape[0], axis=0)


def passe_bande_fft(x, f0, q):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    h = np.exp(-0.5 * (np.log(np.maximum(f, 1) / f0) / q) ** 2)
    return np.fft.irfft(X * (h[:, None] if x.ndim > 1 else h), x.shape[0], axis=0)


def bruit_brun(n):
    b = np.cumsum(rng.standard_normal(n))
    b -= passe_bas_fft(b, 2.0)
    return b / np.max(np.abs(b))


def bruit_rose(n):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X /= np.sqrt(np.maximum(f, 10))
    x = np.fft.irfft(X, n)
    return x / np.max(np.abs(x))


def reverb(x, duree=3.2, clarte=4000, melange=0.35, pre=0.02):
    """Réverbération par convolution avec une réponse impulsionnelle synthétique (stéréo décorrélée)."""
    n = int(duree * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-6.9 * t / duree)[:, None]
    ir = passe_bas_fft(ir, clarte, 1)
    ir[: int(pre * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2, axis=0))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    m = x.shape[0] + n
    taille = 1 << int(np.ceil(np.log2(m)))
    humide = np.fft.irfft(np.fft.rfft(x, taille, axis=0) * np.fft.rfft(ir, taille, axis=0), taille, axis=0)[: x.shape[0]]
    return x * (1 - melange) + humide * melange * 2.2


def pan(x, p):
    """p : -1 gauche, +1 droite (scalaire ou tableau)."""
    p = np.broadcast_to(np.asarray(p, float), x.shape)
    ang = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(ang), x * np.sin(ang)], 1)


def nappe(notes, t0, t1, att=3.0, rel=4.0, brillance=900, niveau=0.1, detune=0.12):
    """Nappe : dents de scie légèrement désaccordées, filtrées, enveloppe lente."""
    out = np.zeros((N, 2))
    i0, i1 = int(t0 * SR), min(int((t1 + rel) * SR), N)
    tt = T[i0:i1] - t0
    e = np.clip(tt / att, 0, 1) ** 1.5 * np.clip((t1 + rel - t0 - tt) / rel, 0, 1)
    for k, note in enumerate(notes):
        f = hz(note)
        for c, d in enumerate((-detune, detune)):
            ph = 2 * np.pi * f * (1 + d / 100) * tt + rng.uniform(0, 6.28)
            scie = 2 * ((ph / (2 * np.pi)) % 1) - 1
            voix = passe_bas_fft(scie, brillance, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * tt + k))
            out[i0:i1, c] += voix * e * niveau / len(notes)
    return out


def cloche(f, duree=3.0, niveau=0.1, brillance=1.0):
    """Note cristalline : synthèse FM (rapport non entier -> timbre de verre), décroissance exponentielle."""
    n = int(duree * SR)
    t = np.arange(n) / SR
    mod = brillance * 2.2 * np.exp(-t * 3.5) * np.sin(2 * np.pi * f * 3.5 * t)
    s = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.2) + 0.25 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4.5)
    s *= np.minimum(t / 0.003, 1)
    return s * niveau


def poser(piste, son, t, p=0.0):
    i = int(t * SR)
    if i >= N:
        return
    s = son[: N - i]
    if s.ndim == 1:
        s = pan(s, p)
    piste[i:i + s.shape[0]] += s


def musique():
    m = np.zeros((N, 2))
    # sous-basse (ré 1) qui respire, plus présente à l'apogée
    sub = np.sin(2 * np.pi * hz("D1") * T) + 0.3 * np.sin(2 * np.pi * hz("D2") * T)
    m += pan(sub * env([(0, 0), (3, 0.16), (12, 0.2), (25, 0.22), (40, 0.28), (57, 0.3), (63, 0.12), (65, 0)]), 0)
    # bourdon grave filtré (ré-la), ouverture progressive du filtre
    m += nappe(["D2", "A2"], 0.0, 61.0, att=4, rel=4, brillance=380, niveau=0.22)
    # textures : quinte haute en souffle filtré
    souffle = passe_bande_fft(bruit_rose(N), 1800, 0.35) * env([(0, 0), (12, 0), (18, 0.05), (40, 0.07), (57, 0.06), (65, 0)])
    m += np.stack([souffle, np.roll(souffle, 1900)], 1)
    # progression : Rém9 -> Si♭maj7 -> Fa/la -> Do sus2 -> ... -> Ré (quinte puis tierce majeure)
    accords = [
        (12.0, 22.0, ["D3", "F3", "A3", "E4"], 650),
        (21.0, 30.0, ["Bb2", "F3", "A3", "D4"], 900),
        (29.0, 37.0, ["F2", "C3", "A3", "E4"], 1300),
        (36.0, 44.0, ["C3", "G3", "D4", "E4"], 1700),
        (43.0, 50.0, ["Bb2", "F3", "D4", "A4"], 2200),
        (49.0, 57.5, ["G2", "D3", "Bb3", "F4", "A4"], 2400),
        (57.0, 61.5, ["D3", "A3", "D4", "F#4", "A4"], 1800),
    ]
    for t0, t1, notes, b in accords:
        niv = 0.11 if t0 < 40 else 0.15
        m += nappe(notes, t0, t1, att=3.5, rel=3.5, brillance=b, niveau=niv)
    # notes cristallines : de plus en plus denses avec la croissance des cristaux
    gamme = ["D5", "E5", "F5", "A5", "C6", "D6", "E6", "A6"]
    temps = []
    t = 13.0
    while t < 57:
        densite = 0.25 if t < 22 else 0.6 if t < 35 else 1.1 if t < 48 else 0.8
        t += rng.exponential(1 / densite) + 0.18
        temps.append(t)
    for t in temps:
        if t > 57:
            break
        note = gamme[rng.integers(0, len(gamme) if t > 30 else 5)]
        niv = 0.035 if t < 25 else 0.05
        poser(m, cloche(hz(note), 3.2, niv, rng.uniform(0.6, 1.2)), t, rng.uniform(-0.6, 0.6))
    # motif de résolution : ré-la-ré-fa# (fin élégante)
    for i, (note, dt) in enumerate((("D5", 0.0), ("A5", 0.55), ("D6", 1.1), ("F#5", 1.75))):
        poser(m, cloche(hz(note), 4.5, 0.07, 0.8), 57.3 + dt, (-0.3, 0.3, 0.0, 0.15)[i])
    m = reverb(m, duree=4.0, clarte=5200, melange=0.4)
    m *= env([(0, 0), (0.8, 1), (63.0, 1), (65, 0)])[:, None]
    return m


def effets():
    e = np.zeros((N, 2))
    # grondement souterrain continu (bruit brun très grave)
    gr = passe_bas_fft(bruit_brun(N), 90, 2)
    gr = gr / np.max(np.abs(gr)) * env([(0, 0), (1, 0.18), (5, 0.22), (7, 0.3), (12, 0.16), (22, 0.12), (40, 0.08), (57, 0.12), (62, 0.08), (65, 0)])
    e += np.stack([gr, np.roll(gr, 2400)], 1)
    # impact discret à l'apparition du texte (00:02)
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    choc = np.sin(2 * np.pi * (55 * np.exp(-t * 2) + 32) * t) * np.exp(-t * 3.0) * 0.55
    choc += passe_bas_fft(rng.standard_normal(n), 700) * np.exp(-t * 18) * 0.25
    poser(e, choc, 2.0)
    # plongée dans la roche (5 -> 7 s) : souffle qui monte, puis pénétration grave et résonance minérale
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    b = bruit_rose(n)
    souffle = sum(passe_bande_fft(b, f0, 0.25) * np.clip(1 - abs(t / 2.3 - k / 6), 0, 1)
                  for k, f0 in enumerate([250, 400, 650, 1000, 1500, 2300, 3200]))
    souffle *= (t / 2.3) ** 2 * np.exp(-np.maximum(t - 2.3, 0) * 12) * 1.4
    poser(e, souffle, 4.7)
    n = int(4 * SR)
    t = np.arange(n) / SR
    reson = (np.sin(2 * np.pi * 41.2 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t) + 0.12 * np.sin(2 * np.pi * 311 * t)) * np.exp(-t * 1.1)
    reson *= np.minimum(t / 0.04, 1) * 0.45
    poser(e, reson, 7.0)
    # circulation des fluides (7 -> 24 s) : bruit filtré, modulations lentes, bulles très discrètes
    i0, i1 = int(6.8 * SR), int(26 * SR)
    n = i1 - i0
    t = np.arange(n) / SR
    eau = passe_bande_fft(bruit_rose(n), 500, 0.6) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.31 * t) * np.sin(2 * np.pi * 0.13 * t + 1))
    eau *= np.clip(t / 2.5, 0, 1) * np.clip((n / SR - t) / 4, 0, 1) * 0.16
    e[i0:i1] += pan(eau, 0.5 * np.sin(2 * np.pi * 0.05 * t))
    for tb in np.sort(rng.uniform(8, 24, 38)):
        f = rng.uniform(500, 1300)
        nb = int(0.06 * SR)
        tt = np.arange(nb) / SR
        bulle = np.sin(2 * np.pi * f * (1 + 4 * tt) * tt) * np.exp(-tt * 70) * 0.05
        poser(e, bulle, tb, rng.uniform(-0.7, 0.7))
    # vibrations cristallines lors de la nucléation (24 -> 46 s)
    for tc in np.sort(rng.uniform(24, 46, 34)):
        f = rng.uniform(2400, 5200)
        nb = int(0.5 * SR)
        tt = np.arange(nb) / SR
        tic = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.51 * tt)) * np.exp(-tt * 14) * 0.022
        poser(e, tic, tc, rng.uniform(-0.8, 0.8))
    # transitions : souffle vers la macro (47,5 s), recul (56,8 s)
    for t0, sens in ((47.2, 1), (56.6, -1)):
        n = int(1.8 * SR)
        t = np.arange(n) / SR
        w = passe_bande_fft(bruit_rose(n), 900 if sens > 0 else 600, 0.5)
        w *= np.sin(np.pi * t / 1.8) ** 2 * 0.3
        poser(e, w, t0, 0.0)
    # résonance finale
    n = int(6 * SR)
    t = np.arange(n) / SR
    fin = (np.sin(2 * np.pi * hz("D2") * t) * 0.5 + np.sin(2 * np.pi * hz("A2") * t) * 0.3) * np.exp(-t * 0.7) * np.minimum(t / 0.3, 1) * 0.3
    poser(e, fin, 59.8)
    e = reverb(e, duree=2.6, clarte=3500, melange=0.3)
    e *= env([(0, 0), (0.3, 1), (64.0, 1), (65, 0)])[:, None]
    return e


def ecrire(x, nom):
    x = x / max(np.max(np.abs(x)), 1e-9) * 0.89
    brut = ICI / f"audio/{nom}.f32"
    x.astype(np.float32).tofile(brut)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(brut),
                    "-c:a", "pcm_s24le", str(ICI / f"audio/{nom}.wav")], check=True)
    brut.unlink()


if __name__ == "__main__":
    (ICI / "audio").mkdir(exist_ok=True)
    ecrire(musique(), "musique")
    ecrire(effets(), "effets")
    print("ok")
