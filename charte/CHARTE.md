# Charte de la série — format vertical 9:16

Proposition initiale, **en attente de validation**. Tout écart ultérieur doit être noté ici avec sa raison.

## Format
- Plateformes : TikTok, Instagram Reels, YouTube Shorts (un seul export commun).
- 1080 × 1920, 9:16, 30 i/s (ou cadence de la source si vidéo fournie).
- Durée : 1 à 3 minutes.
- Export : H.264 High + AAC 48 kHz, `yuv420p`, `+faststart`, MP4.

## Couleurs
| Rôle | Couleur |
|---|---|
| Fond / ambiance | noir violacé `#07050B` → `#1A0F2A` |
| Violet principal (titres, éléments graphiques) | `#7B2CBF` |
| Violet clair (mots-clés des sous-titres) | `#C77DFF` |
| Texte | blanc `#FFFFFF` |

Traitement image : rester fidèle aux couleurs réelles des spécimens. L'ambiance sombre passe par le fond, les vignettages légers et les éléments graphiques, **jamais** par une recoloration des minéraux.

## Sous-titres
- Police : Montserrat SemiBold, 66 px (taille M — à confirmer).
- Blanc, contour noir 3,5 px, ombre douce 2 px. Pas de boîte opaque.
- Centrés horizontalement, marges latérales 150 px (dégage les icônes à droite).
- Ligne de base à ~1 400 px du haut : au-dessus des 25 % inférieurs masqués par l'interface.
- 1 à 2 lignes maximum, ~26 caractères par ligne, coupures aux frontières de sens.
- Un mot-clé en violet clair au maximum par sous-titre, pas systématiquement.
- Texte = paroles exactes de la voix off (transcription automatique puis correction contre le script).
- Modèle : `sous-titres.ass`. Aperçus : `apercus/`.

Les zones masquées sont une approximation raisonnable de l'interface des trois plateformes, pas une garantie : elles évoluent. À vérifier sur un premier export publié en privé.

## Mouvement et transitions
- Zooms / dézooms lents (≈ 3 à 8 % d'échelle par plan, courbe adoucie), ciblés sur des zones choisies dans chaque photo.
- Panoramiques uniquement s'ils révèlent un détail utile.
- Transitions : coupe franche ou fondu court (≈ 0,4 s). Pas de transitions gadget.
- Aucun effet ajouté (particules, flares, glitch…).

## Logo
- Fourni par l'utilisateur (PNG transparent ou SVG).
- Emplacement : à définir à réception — hors zones masquées, discret.

## Audio
- Voix off de l'utilisateur prioritaire ; musique fournie par l'utilisateur, abaissée sous la voix (ducking).
- Cible interne : ≈ −14 LUFS intégré, crêtes ≤ −1 dBTP (cible interne, pas une exigence officielle des plateformes).
- Fondus en entrée et en sortie.
