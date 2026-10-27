# Lussatite, l'opale d'Auvergne — script et découpage

Version 1 — validée par l'auteur le 2026-10-27. Découpage détaillé (cadrages, zooms, titres) : `montage_projet.py`. Format 9:16, 1080 × 1920, cible ≈ 2 min 45 s (voix ≈ 2 min 33 s, 382 mots à ~150 mots/min + générique ≈ 12 s).
Le texte à lire seul est dans `voix_off.txt`. Les minutages sont indicatifs : le montage final suivra votre enregistrement.

Mouvements : zooms/dézooms lents (≈ 3–8 % par plan, courbe adoucie), fondus courts ≈ 0,4 s ou coupes franches. Aucun crédit sur les images : tout est dans le générique final.

| # | ≈ Temps | Voix off | Image | Mouvement |
|---|---|---|---|---|
| 1 | 0:00–0:06 | « Des perles d'opale bleue… nées dans du goudron. Et ça se passe en Auvergne. » | 02 macro perles | Départ serré sur la grosse perle centrale → dézoom lent qui révèle le bitume noir |
| 2 | 0:06–0:18 | « Voici la lussatite… village de Lussat, au nord-est de Clermont-Ferrand. » | 01 ensemble, puis W3 carte postale Lussat 1910 (en cadre) | 01 : lent travelling gauche → droite le long des perles ; W3 : léger zoom avant |
| 3 | 0:18–0:27 | « Oubliez les opales de bijouterie… imprégnée de bitume. » | I3 opale noble → 02 macro | I3 : zoom sur le jeu de couleurs ; coupe franche vers 02 (contraste) |
| 4 | 0:27–0:45 | « En 1890, Ernest Mallard… plus proche d'une opale que du quartz. » | I1 portrait Mallard (médaillon sur fond sombre) | Zoom avant très lent ; texte à l'écran « Ernest Mallard · 1890 » |
| 5 | 0:45–1:02 | « Aujourd'hui, on la range parmi les opales-CT… le C et le T. » | I2 quartz → I3 opale → I4 lussatite | Chaque plan : zoom du spécimen vers le schéma atomique (suit la flèche de l'illustration) ; textes « Quartz : ordonné », « Opale : désordonnée », « Opale-CT » |
| 6 | 1:02–1:30 | « Comment s'est-elle formée ?… elle dépose la lussatite. » | W2 Puy de Mur (Limagne) → I5 coupe → W1 pépérite | W2 : léger dézoom ; I5 : zoom ≈ 1,4× puis défilement de bas en haut avec étiquettes animées (Calcaire bitumineux → Calcaire et marne → Pépérite → Coulée basaltique), puis suivi des flèches bleues ; W1 : zoom sur un fragment de basalte |
| 7 | 1:30–1:50 | « Elle ne forme jamais de beaux cristaux… un peu comme le bleu du ciel. » | 02 (perles, grappes) → 04 (fleur) → 01 (placage, zone blanche à droite) | 02 : zoom sur une grappe ; 04 : zoom sur la rosette du bas ; 01 : zoom sur le placage |
| 8 | 1:50–2:12 | « Les pièces les plus spectaculaires ?… ici, un os de flamant. » | 09 hélix → I4 hélix (vue spécimen seule) → 10 os | 09 : défilement lent de gauche à droite sur les 5 hélix ; 10 : zoom le long de l'os vers la partie bleutée |
| 9 | 2:12–2:30 | « Les plus beaux échantillons viennent de la mine des Rois… détruit en 1969. » | 12 galerie (vous) → W4 galerie (Commons, en cadre) | 12 : lent zoom avant sur les coulées de bitume ; texte « Mine des Rois · Dallet » |
| 10 | 2:30–2:40 | « Méfiez-vous des lussatites vendues en ligne… sa roche d'origine. » | 04 fleur sur matrice (bitume visible) | Dézoom lent qui montre la roche entière |
| 11 | 2:40–2:43 | « Et vous, vous en aviez déjà vu ? » | 02 macro | Zoom avant final, fondu au noir |
| 12 | 2:43–2:55 | — (musique seule) | Générique défilant sur fond noir violacé + logo | Défilement lent, lisible |

## Générique final (défilant)
- Texte, voix, montage : jeremineralogie
- Photos de spécimens et de la mine des Rois, illustrations et schémas : © jeremineralogie
- Ernest Mallard, portrait (XIXe s.) — domaine public, via Wikimedia Commons
- Pépérite du Puy de Crouel — Romain Cadiou, CC BY-SA 3.0, via Wikimedia Commons
- Puy de Mur vu de Dallet — Pierre André Leclercq, CC BY-SA 4.0, via Wikimedia Commons
- Lussat, carte postale (1910) — anonyme, CC0, Bibliothèque Clermont Auvergne Métropole, via Wikimedia Commons
- Galerie de la mine des Rois — Vincent Duseigne, CC BY 2.5, via Wikimedia Commons
- Musique : [à compléter]
- Sources : E. Mallard, Bull. Soc. fr. Minéral. 13 (1890) ; Le Règne Minéral, hors-série (2015) ; Mindat ; Encyclopaedia Britannica

## Points ouverts
- Rosette concentrique : rose de calcédoine du Brésil (confirmé par l'auteur) → plan « Méfiez-vous ».
- Logo : reçu, utilisé en fin de générique. Musique : à fournir.
- Voix off : à enregistrer par l'auteur (la maquette utilise une voix de synthèse provisoire).
- Helix ramondi : nom courant chez les collectionneurs ; nomenclature actuelle non vérifiée.
- Os de flamant : identification fournie par l'auteur.
- Agate au microscope (Imaggeo, CC BY-NC-ND 3.0) : exclue — licence « pas de modification » incompatible avec une vidéo, et ce n'est pas de la lussatite.

## Fabrication
- Maquette (voix de synthèse provisoire) : `python3 projets/lussatite/montage_projet.py maquette`
- Version finale :
  1. déposer la voix dans `sources/voix_off.wav` ;
  2. `python3 outils/transcrire.py projets/lussatite/sources/voix_off.wav projets/lussatite/exports/_travail/voix_off_mots.json` ;
  3. `python3 projets/lussatite/montage_projet.py finale` ;
  4. `outils/verifier.sh projets/lussatite/exports/lussatite_v1_finale_9x16.mp4`.
