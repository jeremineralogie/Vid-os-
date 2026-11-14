"""Musique d'ambiance originale de la promo (23 s), synthétisée, calée sur les transitions du montage.

Réutilise les instruments de projets/fluorite_caillou/musique.py (nappes, cloches FM, réverbération).
python3 musique.py -> audio/musique.wav
"""
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "fluorite_caillou"))
import musique as mu  # noqa: E402

DUREE = 23.0
mu.DUREE = DUREE
mu.N = int(mu.SR * DUREE)
mu.T = np.arange(mu.N) / mu.SR
SR, N, T = mu.SR, mu.N, mu.T

BPM = 96
TEMPS = 60 / BPM
GLISSES = [2.85, 5.9, 12.3]       # transitions « glissé »
MORPHES = [9.45, 15.75]           # carte -> fiche
LOGO = 19.3


def kick(niveau=0.5):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (48 + 70 * np.exp(-t * 28)) * t) * np.exp(-t * 9) * niveau


def pincé(f, niveau=0.08):
    """Corde pincée douce (Karplus-Strong simplifié)."""
    n = int(1.4 * SR)
    p = int(SR / f)
    buf = np.random.default_rng(int(f)).uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * niveau


def souffle(duree=0.6, niveau=0.35):
    n = int(duree * SR)
    t = np.arange(n) / SR
    b = mu.bruit_rose(n)
    s = sum(mu.passe_bande_fft(b, f0, 0.3) * np.clip(1 - abs(t / duree - k / 4), 0, 1)
            for k, f0 in enumerate([500, 1100, 2200, 3800, 5200]))
    return s * np.sin(np.pi * t / duree) ** 2 * niveau


def main():
    m = np.zeros((N, 2))
    # nappe : ré mineur -> si bémol -> fa -> do -> résolution sur ré (quinte + 9e) au logo
    for t0, t1, notes, b in [(0.0, 6.0, ["D3", "A3", "F4", "E4"], 900), (5.6, 12.4, ["Bb2", "F3", "D4", "A4"], 1300),
                             (12.0, 15.9, ["F2", "C3", "A3", "E4"], 1600), (15.6, 19.4, ["C3", "G3", "D4", "E4"], 1900),
                             (19.1, 23.0, ["D3", "A3", "D4", "E4", "A4"], 1500)]:
        m += mu.nappe(notes, t0, t1, att=0.9, rel=1.8, brillance=b, niveau=0.17)
    m += mu.pan(np.sin(2 * np.pi * mu.hz("D1") * T) * mu.env([(0, 0), (1, 0.12), (18.8, 0.16), (19.4, 0.22), (22, 0.1), (23, 0)]), 0)
    # pulsation douce à partir de l'apparition du site (2,85 s), pause sur le logo
    t = 2.85
    while t < 18.8:
        mu.poser(m, kick(0.42), t, 0.0)
        t += TEMPS
    # arpège pincé (ré mineur pentatonique), une croche sur deux
    gamme = ["D4", "F4", "G4", "A4", "C5", "D5", "F5", "A5"]
    rng = np.random.default_rng(3)
    t, k = 2.85, 0
    while t < 18.8:
        if k % 2 == 0 or rng.random() < 0.35:
            mu.poser(m, pincé(mu.hz(gamme[(k * 3 + rng.integers(0, 3)) % len(gamme)]), 0.07), t, rng.uniform(-0.5, 0.5))
        t += TEMPS / 2
        k += 1
    # ouverture : note de verre sur la photo, puis petite montée vers le site
    mu.poser(m, mu.cloche(mu.hz("A5"), 3.0, 0.09, 1.0), 0.15, -0.2)
    mu.poser(m, mu.cloche(mu.hz("D6"), 2.5, 0.06, 0.9), 1.4, 0.3)
    # transitions : souffles sur les glissés, cloches sur les passages carte -> fiche
    for g in GLISSES:
        mu.poser(m, souffle(0.6, 0.3), g - 0.12, 0.0)
    for g, note in zip(MORPHES, ["E6", "A5"]):
        mu.poser(m, mu.cloche(mu.hz(note), 2.5, 0.08, 1.1), g, 0.2)
    # logo : accord cristallin qui se résout
    for i, (note, dt) in enumerate((("D5", 0.0), ("A5", 0.18), ("D6", 0.36), ("E6", 0.6))):
        mu.poser(m, mu.cloche(mu.hz(note), 3.5, 0.08, 0.8), LOGO + dt, (-0.3, 0.3, 0.0, 0.15)[i])
    m = mu.reverb(m, duree=2.8, clarte=5500, melange=0.32)
    m *= mu.env([(0, 0), (0.15, 1), (21.8, 1), (23.0, 0)])[:, None]
    (ICI / "audio").mkdir(exist_ok=True)
    m = m / np.max(np.abs(m)) * 0.89
    brut = ICI / "audio/musique.f32"
    m.astype(np.float32).tofile(brut)
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(brut),
                    "-c:a", "pcm_s24le", str(ICI / "audio/musique.wav")], check=True)
    brut.unlink()
    print("ok")


main()
