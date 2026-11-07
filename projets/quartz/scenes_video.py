"""Compose chaque séquence HyperFrames à la durée exacte de son plan, puis la rend (sources/hf/<nom>.mp4).

python3 projets/quartz/scenes_video.py            -> toutes les séquences
python3 projets/quartz/scenes_video.py fer_3d     -> une seule
"""
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "outils"))
sys.path.insert(0, str(ICI))
import illustrations  # noqa: E402
import montage  # noqa: E402
import montage_projet  # noqa: E402
import realiste  # noqa: E402

projet = montage_projet.projet()
plages, _ = montage.plages(projet)
demandes = [a for a in sys.argv[1:] if not a.startswith("-")]
(ICI / "sources" / "hf").mkdir(parents=True, exist_ok=True)
for plan, (a, b) in zip(projet.plans, plages):
    nom = Path(plan.image).stem
    if plan.mode != "video" or (demandes and nom not in demandes):
        continue
    duree = round(b - a, 2)
    d = illustrations.composer(nom, duree) if nom == "synthese" else realiste.composer(nom, duree)
    subprocess.run(["npx", "--yes", realiste.VERSION, "render", str(d), "-q", "delivery", "--fps", "30",
                    "-o", str(ICI / "sources" / "hf" / f"{nom}.mp4"), "--quiet"], check=True)
    print("rendu", nom, duree, "s")
