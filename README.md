# Vid-os

Outils et skills Claude Code pour le montage vidéo et la création de contenu social.

## Skills

- [`video-creator-pro`](.claude/skills/video-creator-pro/SKILL.md) — workflow de montage professionnel et reproductible pour TikTok, Reels, Shorts et YouTube : inventaire des médias, plan de rétention, sous-titres en zone sûre, mixage audio, identité visuelle cohérente, profils d'export et vérifications (`ffprobe`, test de décodage), sans faits inventés.

La charte de la série (couleurs, sous-titres, mouvements, export) est dans [`charte/CHARTE.md`](charte/CHARTE.md).

Claude Code charge automatiquement les skills placés dans `.claude/skills/` lorsqu'il travaille dans ce dépôt. Pour l'utiliser dans tous vos projets, copiez le dossier dans `~/.claude/skills/`.

## Outils de montage
- `outils/montage.py` : moteur de montage 9:16 (plans animés calés sur la voix off, sous-titres de la charte, titres, générique défilant avec logo).
- `outils/transcrire.py` : horodatage mot à mot d'une voix off (faster-whisper).
- `outils/verifier.sh` : contrôles d'export (métadonnées, décodage, noirs, sonie).

Les médias sources et les exports vidéo ne sont pas versionnés (dépôt public).
