#!/bin/bash
# Rendu de tous les plans (reprise possible : les images déjà rendues sont conservées).
cd "$(dirname "$0")"
B="xvfb-run -a blender -b -P"
$B blender/exterieur.py -- rendu 1 226 2>&1 | grep --line-buffered -E "Saved|Error|Traceback"
$B blender/interieur.py -- rendu 205 1755 2>&1 | grep --line-buffered -E "Saved|Error|Traceback"
$B blender/exterieur.py -- rendu 1715 1950 2>&1 | grep --line-buffered -E "Saved|Error|Traceback"
echo RENDU_TERMINE
