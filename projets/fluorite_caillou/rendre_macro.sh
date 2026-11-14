#!/bin/bash
# Recalcul de la macro (48 -> 56,7 s) après correction de la hauteur de caméra.
cd "$(dirname "$0")"
while pgrep -f rendre_suite.sh >/dev/null; do sleep 15; done
for f in $(seq 1441 1700); do rm -f sources/rendu/int_$(printf %04d $f).png; done
xvfb-run -a blender -b -P blender/interieur.py -- rendu 1441 1700 2>&1 | grep --line-buffered -E "Saved|Error|Traceback"
echo MACRO_TERMINE
