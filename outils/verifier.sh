#!/usr/bin/env bash
# Contrôles d'export : métadonnées, décodage complet, début/fin noirs, sonie, écrêtage.
# Usage : outils/verifier.sh fichier.mp4
set -euo pipefail
f="$1"

echo "== Métadonnées"
ffprobe -v error -show_entries stream=codec_type,codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels,bit_rate \
  -show_entries format=duration,size,bit_rate -of default=nw=1 "$f"

echo "== Décodage complet"
if ffmpeg -v error -i "$f" -f null - 2>&1 | grep -q .; then echo "ERREURS de décodage"; else echo "OK, aucune erreur"; fi

echo "== Images noires (>= 0,5 s)"
ffmpeg -v info -i "$f" -vf blackdetect=d=0.5:pix_th=0.06 -an -f null - 2>&1 | grep -o "black_start.*" || echo "aucune"

echo "== Sonie (EBU R128) et crêtes"
ffmpeg -v info -i "$f" -vn -af ebur128=peak=true -f null - 2>&1 | grep -A12 "Summary:" | grep -E "I:|LRA:|Peak:"
