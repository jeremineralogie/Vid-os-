"""Voix off de synthèse plus naturelle : phrase par phrase, pauses variées, respirations, ambiance.

python3 outils/voix_synthese.py texte.txt voix.wav mots.json [voix] [débit]

Voix de synthèse (Microsoft, via edge-tts) : à signaler comme telle au générique et sur les
plateformes. Les respirations et l'ambiance sont générées (bruit filtré), pas enregistrées.
"""
import asyncio
import json
import random
import re
import ssl
import subprocess
import sys

import edge_tts
import edge_tts.communicate
import numpy as np

SR = 48000
# le proxy de l'environnement présente son propre certificat
edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")


def decoder_mp3(donnees):
    brut = subprocess.run(["ffmpeg", "-v", "error", "-i", "-", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                          input=donnees, capture_output=True, check=True).stdout
    return np.frombuffer(brut, np.float32).copy()


async def synthetiser(phrase, voix, debit):
    com = edge_tts.Communicate(phrase, voix, rate=debit, boundary="WordBoundary")
    audio, mots = bytearray(), []
    async for morceau in com.stream():
        if morceau["type"] == "audio":
            audio += morceau["data"]
        elif morceau["type"] == "WordBoundary":
            mots.append({"t": morceau["offset"] / 1e7, "d": morceau["duration"] / 1e7, "w": morceau["text"]})
    return decoder_mp3(bytes(audio)), mots


def bruit_rose(n, rng):
    spectre = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spectre /= np.sqrt(np.maximum(f, 20))
    son = np.fft.irfft(spectre, n)
    return son / np.max(np.abs(son))


def respiration(rng):
    """Inspiration discrète par le nez/la bouche : bruit rose filtré, enveloppe montante."""
    duree = rng.uniform(0.32, 0.48)
    n = int(duree * SR)
    spectre = np.fft.rfft(bruit_rose(n, rng))
    f = np.fft.rfftfreq(n, 1 / SR)
    centre = rng.uniform(900, 1400)
    spectre *= np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(centre)) / 0.75) ** 2)
    son = np.fft.irfft(spectre, n)
    t = np.linspace(0, 1, n)
    enveloppe = np.where(t < 0.65, np.sin(np.pi / 2 * t / 0.65) ** 2, np.cos(np.pi / 2 * (t - 0.65) / 0.35) ** 2)
    son = son * enveloppe
    return son / np.max(np.abs(son)) * 10 ** (rng.uniform(-31, -27) / 20)


def rogner(audio, mots, seuil=0.004):
    """Retire les silences de début/fin ajoutés par la synthèse, en recalant les mots."""
    actif = np.flatnonzero(np.abs(audio) > seuil)
    if actif.size == 0:
        return audio, mots
    debut = max(actif[0] - int(0.02 * SR), 0)
    fin = min(actif[-1] + int(0.06 * SR), audio.size)
    decal = debut / SR
    return audio[debut:fin], [dict(m, t=max(m["t"] - decal, 0)) for m in mots]


def fabriquer(texte, sortie_wav, sortie_mots, voix="fr-FR-RemyMultilingualNeural", debit="-4%"):
    rng = np.random.default_rng(7)
    alea = random.Random(7)
    paragraphes = [p.strip() for p in texte.split("\n\n") if p.strip()]
    pistes, mots, curseur = [], [], 0.25

    def poser(son, a):
        pistes.append((int(a * SR), son))

    for i, paragraphe in enumerate(paragraphes):
        phrases = re.split(r"(?<=[.?!…])\s+(?=[A-ZÀ-Ý«])", paragraphe)
        for j, phrase in enumerate(phrases):
            nouvelle_respiration = (i > 0 and j == 0) or (j > 0 and len(phrase.split()) > 16)
            if nouvelle_respiration:
                souffle = respiration(rng)
                poser(souffle, curseur)
                curseur += souffle.size / SR + alea.uniform(0.06, 0.12)
            # léger écart de débit d'une phrase à l'autre, comme à l'oral
            ecart = int(debit.rstrip("%")) + alea.choice([-2, -1, 0, 0, 1])
            audio, m = asyncio.run(synthetiser(phrase, voix, f"{ecart:+d}%"))
            audio, m = rogner(audio, m)
            poser(audio, curseur)
            mots += [dict(x, t=x["t"] + curseur) for x in m]
            curseur += audio.size / SR
            fin = phrase.rstrip()[-1]
            curseur += alea.uniform(0.42, 0.58) if fin in "?…" else alea.uniform(0.26, 0.4)
        curseur += alea.uniform(0.25, 0.4)  # fin de paragraphe

    total = np.zeros(int((curseur + 0.5) * SR), np.float32)
    for debut, son in pistes:
        total[debut:debut + son.size] += son
    total += bruit_rose(total.size, rng).astype(np.float32) * 10 ** (-62 / 20)  # ambiance de pièce

    brut = sortie_wav + ".brut.f32"
    total.astype(np.float32).tofile(brut)
    # timbre : coupe du grave inutile, un peu de chaleur, compression douce, légère présence
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", brut,
        "-af", "highpass=f=70,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3500:t=q:w=1.5:g=1.5,"
               "equalizer=f=7000:t=q:w=2:g=-2,acompressor=threshold=-22dB:ratio=2.2:attack=12:release=180,"
               "aecho=0.9:0.9:18|31:0.07|0.04,loudnorm=I=-16:TP=-1.5:LRA=8",
        "-ar", str(SR), "-ac", "2", sortie_wav], check=True)
    subprocess.run(["rm", "-f", brut])
    with open(sortie_mots, "w", encoding="utf-8") as f:
        json.dump(mots, f, ensure_ascii=False)
    return curseur


if __name__ == "__main__":
    texte = open(sys.argv[1], encoding="utf-8").read()
    duree = fabriquer(texte, sys.argv[2], sys.argv[3], *sys.argv[4:])
    print(f"Voix : {duree:.1f} s -> {sys.argv[2]}")
