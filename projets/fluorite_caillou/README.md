# Ce que tu ne vois pas dans un simple caillou

Documentaire vertical de 65 s (1080 × 1920, 30 i/s, 1 950 images) sur la formation hydrothermale de la fluorite. Tout est généré par programme : l'animation 3D (Blender), la voix (synthèse), la musique et les effets (numpy).

## Organisation

| Fichier | Rôle |
|---|---|
| `voix_off.txt` | Script de la voix off, un paragraphe par séquence |
| `voix.py` | Synthèse de la voix (edge-tts, `fr-FR-RemyMultilingualNeural`), un fichier par séquence, avec les mots horodatés |
| `musique.py` | Musique originale et effets sonores (synthèse : nappes, sous-basse, notes FM cristallines, grondements, souffles, réverbération par convolution) |
| `blender/fl.py` | Matériaux (roche, fluorite, fluide) et outils communs |
| `blender/exterieur.py` | Bloc de roche : apparition, plongée (0-7,5 s) et recul final (57-65 s) |
| `blender/interieur.py` | Plan continu : fracture, fluides, cavité, croissance des cristaux, ions, macro (6,8-58,5 s) |
| `rendre_tout.sh` | Rendu de toutes les images (reprise possible) |
| `assembler.py` | Fondus, étalonnage, titres et sous-titres karaoké (ASS), logo, mixage, export H.264 |
| `miniature.py` | Couverture verticale |
| `SOURCES.md` | Faits vérifiés et sources à citer en description |

Les dossiers `audio/`, `sources/` (rendus, logo) et `exports/` ne sont pas versionnés.

## Régénérer

```bash
python3 voix.py                 # audio/seg_1..7.wav + .json
python3 musique.py              # audio/musique.wav, audio/effets.wav
./rendre_tout.sh                # sources/rendu/*.png (environ 6 h en rendu logiciel, 4 cœurs)
python3 assembler.py            # exports/JEREMINERALOGIE_CE_QUE_TU_NE_VOIS_PAS.mp4
python3 miniature.py            # exports/MINIATURE_CE_QUE_TU_NE_VOIS_PAS.jpg
```

Les aperçus se font sans rendre l'animation entière : `blender -b -P blender/interieur.py -- apercu 30,41,50 50` (instants en secondes, échelle en %).

## Modifier

- **Texte et timing de la voix :** `voix_off.txt`, puis `voix.py`. Les départs de chaque paragraphe sont dans `VOIX` (`assembler.py`).
- **Titres à l'écran :** liste `TITRES` (`assembler.py`). Les mots-clés en violet sont dans `MOTS_CLES`.
- **Caméra :** `animer_camera` (intérieur, positions clés `cles`) et `pos_a` / `pos_c` (extérieur).
- **Cristaux :** `generations` (nombre, tailles, dates de nucléation, durée de croissance) ; couleur et transparence dans `mat_fluorite`.
- **Mixage :** volumes de la musique et des effets, atténuation sous la voix (`filtre_audio`).

## Choix techniques

L'environnement n'a pas de carte graphique : Eevee tourne en rendu logiciel (llvmpipe), à environ 12 s par image à 810 × 1440. Les images sont agrandies en 1080 × 1920 (Lanczos) au montage. Cycles (lancer de rayons) donnerait des réfractions exactes mais demanderait plus de 30 h. La fluorite est donc rendue par une transparence teintée avec reflets de Fresnel, et sa zonation par un cœur plus coloré visible au travers.
