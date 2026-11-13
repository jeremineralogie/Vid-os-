"""Voix off de synthèse, une séquence par paragraphe, mesurée pour caler la timeline.
python3 voix.py -> audio/seg_<n>.wav + audio/seg_<n>.json (mots horodatés)
"""
import asyncio, json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
import voix_synthese as vs

ICI = Path(__file__).resolve().parent
VOIX, DEBIT = "fr-FR-RemyMultilingualNeural", -3

def main():
    paras = [p.strip() for p in (ICI / "voix_off.txt").read_text(encoding="utf-8").split("\n\n") if p.strip()]
    for i, p in enumerate(paras):
        phrases = re.split(r"(?<=[.?!…])\s+(?=[A-ZÀ-Ý«])", p)
        morceaux, mots, t = [], [], 0.0
        for j, ph in enumerate(phrases):
            a, m = asyncio.run(vs.synthetiser(ph, VOIX, f"{DEBIT:+d}%"))
            a, m = vs.rogner(a, m)
            morceaux.append(a); mots += [dict(x, t=x["t"] + t) for x in m]
            t += a.size / vs.SR
            if j < len(phrases) - 1:
                pause = 0.34
                morceaux.append(np.zeros(int(pause * vs.SR), np.float32)); t += pause
        son = np.concatenate(morceaux)
        brut = ICI / f"audio/seg_{i+1}.f32"; son.astype(np.float32).tofile(brut)
        import subprocess
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", str(brut),
            "-af", "highpass=f=70,equalizer=f=150:t=q:w=1:g=2.5,equalizer=f=3500:t=q:w=1.5:g=1.5,equalizer=f=7000:t=q:w=2:g=-2,"
                   "acompressor=threshold=-22dB:ratio=2.2:attack=12:release=180",
            str(ICI / f"audio/seg_{i+1}.wav")], check=True)
        brut.unlink()
        (ICI / f"audio/seg_{i+1}.json").write_text(json.dumps(mots, ensure_ascii=False), encoding="utf-8")
        print(i + 1, f"{t:.2f} s", len(p.split()), "mots")

main()
