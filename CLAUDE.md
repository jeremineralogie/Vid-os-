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
- **Crédits :** aucun crédit sur les images. Un générique défilant en fin de vidéo regroupe toutes les sources ; les photos de l'auteur sont créditées « © jeremineralogie ». Le logo apparaît à la fin.
- **Plans :** photos en plein cadre pour les formats portrait, en « carte » arrondie sur fond de charte pour les formats paysage. Zooms lents et doux, fondus de 0,4 s, titres courts en haut de l'écran.
- **Faits :** ne rien ajouter qui ne figure pas dans l'article. Formulations prudentes (« nommée par », non « découverte par », sans preuve). Toute image générée ou illustrative doit être annoncée comme telle.

## Fichiers
- `outils/montage.py` : moteur réutilisable. Chaque projet a son `projets/<nom>/montage_projet.py`, avec des plans calés sur les premiers mots d'une phrase du texte.
- `projets/<nom>/sources/` et `exports/` ne sont **pas versionnés** (dépôt public) : ne jamais pousser les photos ni les vidéos.
- Exemple complet : `projets/lussatite/`.
