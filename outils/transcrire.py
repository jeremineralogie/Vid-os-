"""Horodatage mot à mot d'une voix off (faster-whisper), au format attendu par montage.py.

python3 outils/transcrire.py voix.wav mots.json [modèle]

Le texte affiché reste celui du script (accents, noms propres) : la transcription ne sert
qu'à savoir quand chaque mot est prononcé. Les mots de faible confiance sont signalés.
"""
import json
import sys

from faster_whisper import WhisperModel


def transcrire(audio, sortie, modele="medium"):
    whisper = WhisperModel(modele, device="cpu", compute_type="int8")
    segments, _ = whisper.transcribe(audio, language="fr", word_timestamps=True, vad_filter=True)
    mots, douteux = [], []
    for seg in segments:
        for m in seg.words:
            mots.append({"t": m.start, "d": m.end - m.start, "w": m.word.strip()})
            if m.probability < 0.5:
                douteux.append(f"{m.start:7.2f}s  {m.word.strip()}  ({m.probability:.2f})")
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(mots, f, ensure_ascii=False)
    print(f"{len(mots)} mots horodatés -> {sortie}")
    if douteux:
        print("À vérifier à l'écoute (reconnaissance incertaine) :")
        print("\n".join(douteux))


if __name__ == "__main__":
    transcrire(*sys.argv[1:])
