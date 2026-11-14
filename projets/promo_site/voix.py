"""Voix de synthèse (edge-tts, fr-FR-RemyMultilingualNeural), phrase par phrase, mots horodatés.
python3 voix.py -> audio/voix.wav, audio/voix.json
"""
import asyncio, json, re, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
import voix_synthese as vs

ICI = Path(__file__).resolve().parent
# départ de chaque phrase dans la vidéo (s), calé sur le découpage validé
DEPARTS = [0.35, 2.75, 6.4, 13.2, 19.7]

texte = (ICI / "voix_off.txt").read_text(encoding="utf-8").strip()
phrases = re.split(r"(?<=[.?!])\s+", texte)
mots, pistes = [], []
for i, ph in enumerate(phrases):
    a, m = asyncio.run(vs.synthetiser(ph, "fr-FR-RemyMultilingualNeural", "+2%"))
    a, m = vs.rogner(a, m)
    d = DEPARTS[i]
    pistes.append((int(d * vs.SR), a))
    mots += [dict(x, t=x["t"] + d) for x in m]
    print(f"{d:6.2f} -> {d + a.size / vs.SR:6.2f}  {ph}")
total = np.zeros(int(23.5 * vs.SR), np.float32)
for debut, a in pistes:
    total[debut:debut + a.size] += a
brut = ICI / "audio/voix.f32"; total.tofile(brut)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", str(brut),
    "-af", "highpass=f=70,equalizer=f=150:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1.5:g=1.5,acompressor=threshold=-22dB:ratio=2.2:attack=12:release=180",
    str(ICI / "audio/voix.wav")], check=True)
brut.unlink()
(ICI / "audio/voix.json").write_text(json.dumps(mots, ensure_ascii=False), encoding="utf-8")
