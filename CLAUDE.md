# Vid-os — mémoire de production (série jeremineralogie)

Lire avant toute nouvelle vidéo. Ces choix ont été validés par l'auteur sur la vidéo « Lussatite, l'opale d'Auvergne » (oct. 2026) et s'appliquent à toute la série, sauf demande contraire.

## Méthode (skill `video-creator-pro`)
1. L'auteur fournit un article complet et ses photos. Lire l'article, vérifier les faits sensibles et signaler les points douteux. Retirer tout passage qui accuse des personnes identifiables (risque de diffamation).
2. Inventorier les photos, puis poser des questions précises : provenance, ce qui doit être montré en zoom, image réelle ou illustration.
3. Pour les images manquantes, proposer des images libres (Wikimedia Commons en priorité) en vérifiant auteur, licence et définition. Exclure les licences ND, et NC si la chaîne est monétisée. Les photos de Mindat, du Comptoir Géologique ou des marchands ne s'utilisent qu'avec une autorisation écrite. Wikimedia bloque les téléchargements depuis le serveur : demander à l'auteur de télécharger les fichiers.
4. Écrire le script (`voix_off.txt`, environ 380 mots pour environ 2 min 30) et le découpage (`SCRIPT.md`), puis **attendre la validation** de l'auteur.
5. Monter une **maquette avec voix de synthèse provisoire** (edge-tts, voix `fr-FR-HenriNeural` ; le certificat du proxy est corrigé dans le script de synthèse) pour valider les images et le rythme.
6. Version finale : voix de l'auteur, horodatée par `outils/transcrire.py`, plus la musique fournie par l'auteur, abaissée sous la voix.
   Variante demandée par l'auteur : voix de synthèse travaillée (`outils/voix_synthese.py`, voix `fr-FR-RemyMultilingualNeural`, phrase par phrase, pauses variées, respirations générées, traitement du timbre). Elle doit être créditée comme synthèse vocale au générique, et signalée comme contenu généré par IA sur les plateformes si leurs règles l'exigent.
7. Lancer `outils/verifier.sh` et rédiger un compte rendu honnête de ce qui a été vérifié et de ce qui reste à faire.

## Choix validés
- **Format :** uniquement du vertical 9:16 (TikTok, Reels, Shorts), 1080 × 1920, de 1 à 3 minutes, une seule vidéo par article.
- **Voix off :** enregistrée par l'auteur. **Musique et logo :** fournis par l'auteur (`LOGO_jeremineralogie.jpg`, fond sombre, fondu en cercle).
- **Identité :** fond noir violacé (`#0B0710` → `#1A0F2A`), violet `#7B2CBF`, violet clair `#C77DFF`. Ne jamais modifier les couleurs réelles des minéraux. Détails dans `charte/CHARTE.md`.
- **Sous-titres :** Montserrat SemiBold, taille M (66), blancs avec contour noir, centrés, ligne de base vers 1 400 px. Jamais en bas ni à gauche. Deux lignes maximum, mots-clés en violet clair à leur première apparition.
- **Crédits :** aucun crédit sur les images. Depuis La Barre (oct. 2026), l'auteur cite les sources dans la **description** de la vidéo : pas de générique de sources, fin sur le logo seul. (La lussatite garde son générique défilant.)
- **Voix et musique :** à confirmer pour chaque vidéo. La Barre est **muette** (texte à l'écran seul, durée calée sur le temps de lecture).
- **Sujets à ne pas aborder :** l'accès aux anciennes mines (entrées, visites, prospection), même si l'article en parle.
- **Depuis Montebras (oct. 2026) :**
  - Sous-titres **karaoké** : chaque mot passe du gris au blanc au rythme de lecture (`Projet(karaoke=True)`). Contour de 4,5 ; voile renforcé à 0,68 sur les photos claires.
  - Les **informations chiffrées** et les **compositions chimiques** sont animées avec **HyperFrames**. Chaque séquence est composée à la durée exacte de son plan, puis insérée comme `Plan(..., "video")`. Voir `projets/montebras/hyperframes_scenes.py`.
  - Les éléments animés restent dans la zone x 110-970, y 250-1120. Aucun texte ne recouvre un autre texte, et aucun texte n'entre dans les marges des réseaux.
  - **Chaque fait affiché est vérifié** et consigné dans `SOURCES.md`, avec la source à citer en description.
- **Depuis Uranium (oct. 2026) :**
  - Le karaoké est un peu plus rapide : `mots_lecture(par_mot=0.32, base=0.75)`.
  - Les fiches chimiques ont la photo du minéral en fond (assombrie), sous une carte translucide.
  - Un compteur HyperFrames accompagne chaque chiffre affiché.
  - Fin sur le logo avec **jeremineralogie.fr** en dessous (`Projet(texte_logo=...)`).
  - L'auteur ne veut pas de vues aériennes IGN. Archives privilégiées : rapports du CEA numérisés (OSTI/ETDEWEB).
- **Depuis Barytes (oct. 2026) :**
  - **Toujours une image en rapport avec le sujet en fond, jamais de fond violet.** Les plans « carte » utilisent `Plan(fond="flou")`, c'est-à-dire leur image floutée et assombrie. Les séquences HyperFrames, même chiffrées, ont une photo ou un document en fond.
  - Quand une vidéo présente plusieurs gisements, elle montre une carte du département avec un point et une photo par gisement, qui apparaissent l'un après l'autre (voir `projets/barytes/hyperframes_scenes.py`, `carte_gisements`). Les points sont placés sur la commune, jamais sur l'emplacement précis du gisement.
  - Le minéral s'écrit toujours **« baryte »**, avec un Y : jamais « barytine » ni « barite » à l'écran.
  - Illustrer avec des portraits de savants et des documents anciens du domaine public : archive.org, Wellcome Collection, musée de Cleveland. Le serveur ne peut pas télécharger Wikimedia Commons ni Gallica.
  - Cartes géologiques : services WMS du BRGM (`geoservices.brgm.fr/geologie`), cartes scannées au 1/50 000, harmonisées et au 1/1 000 000. Données BRGM en Licence Ouverte, à citer en description.
  - Ne pas utiliser Planet-Terre (ENS Lyon).
- **Depuis Fluorites (oct. 2026) :**
  - Pour une vidéo à plusieurs gisements dans plusieurs départements : **carte de France lisible, en relief** (estompage IGN, mer et voisins sombres, limites des départements), pas de carte géologique. Pour chaque gisement : dézoom, le point apparaît, zoom sur le département (fond détaillé), chiffres clés avec compteurs, puis les photos. Voir `projets/fluorites/` (`gisements.py`, `carte_fond.py`, `hyperframes_scenes.py`).
  - Le minéral s'écrit **« fluorite »** à l'écran, et non « fluorine ».
  - Les chiffres affichés viennent du mémento BRGM ou des notices à 1/50 000, pas de l'inventaire GITES, dont les productions ne concordent pas.
- **Plans :** photos en plein cadre pour les formats portrait, en « carte » arrondie sur fond de charte pour les formats paysage. Zooms lents et doux, fondus de 0,4 s, titres courts en haut de l'écran.
- **Faits :** ne rien ajouter qui ne figure pas dans l'article. Formulations prudentes (« nommée par », non « découverte par », sans preuve). Toute image générée ou illustrative doit être annoncée comme telle.

## Fichiers
- `outils/montage.py` : moteur réutilisable. Chaque projet a son `projets/<nom>/montage_projet.py`, avec des plans calés sur les premiers mots d'une phrase du texte.
- `projets/<nom>/sources/` et `exports/` ne sont **pas versionnés** (dépôt public) : ne jamais pousser les photos ni les vidéos.
- Exemple complet : `projets/lussatite/`.
