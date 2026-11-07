"""Débruitage des rendus Cycles (Blender de la distribution sans OpenImageDenoise) : moyennes non locales OpenCV.

python3 projets/quartz/debruiter.py nom1 nom2 ...   -> remplace sources/rendus/<nom>.png (l'original est gardé en <nom>_brut.png)
"""
import shutil
import sys
from pathlib import Path

import cv2

RENDUS = Path(__file__).resolve().parent / "sources" / "rendus"
for nom in sys.argv[1:]:
    src, brut = RENDUS / f"{nom}.png", RENDUS / f"{nom}_brut.png"
    if not brut.exists():
        shutil.copy(src, brut)
    img = cv2.imread(str(brut))
    cv2.imwrite(str(src), cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21))
    print("débruité", nom)
