"""Géométrie du quartz α, commune à toutes les scènes Blender.

Groupe d'espace P3₂21 ; a = 4,9134 Å, c = 5,4052 Å ; Si en 3a (x = 0,4697) ; O en 6c (0,4135 ; 0,2669 ; 0,1191).
Contrôle intégré : chaque Si a 4 O à 1,604 et 1,613 Å, chaque O est lié à 2 Si (valeurs publiées : 1,605 et 1,614 Å).
"""
import math

from mathutils import Vector

A, C = 4.9134, 5.4052
OPS = [lambda x, y, z: (x, y, z), lambda x, y, z: (-y, x - y, z + 2 / 3), lambda x, y, z: (-x + y, -x, z + 1 / 3),
       lambda x, y, z: (y, x, -z + 2 / 3), lambda x, y, z: (x - y, -y, -z), lambda x, y, z: (-x, -x + y, -z + 1 / 3)]
LIAISON = 1.7  # seuil Si–O en Å


def _norm(c):
    c = c % 1.0
    return 0.0 if abs(c - 1) < 1e-6 or abs(c) < 1e-6 else c


def orbite(p):
    vus = []
    for op in OPS:
        q = tuple(_norm(v) for v in op(*p))
        if not any(all(min(abs(q[i] - r[i]), 1 - abs(q[i] - r[i])) < 1e-4 for i in range(3)) for r in vus):
            vus.append(q)
    return vus


def cart(f):
    x, y, z = f
    return Vector((A * (x - 0.5 * y), A * (math.sqrt(3) / 2) * y, C * z))


SI_F = orbite((0.4697, 0.0, 0.0))
O_F = orbite((0.4135, 0.2669, 0.1191))
assert len(SI_F) == 3 and len(O_F) == 6


def reseau(n=(6, 6, 2)):
    """Positions cartésiennes (Å) de tous les Si et O sur n mailles (plus une maille de marge)."""
    si, o = [], []
    for i in range(-1, n[0] + 1):
        for j in range(-1, n[1] + 1):
            for k in range(-1, n[2] + 1):
                si += [cart((f[0] + i, f[1] + j, f[2] + k)) for f in SI_F]
                o += [cart((f[0] + i, f[1] + j, f[2] + k)) for f in O_F]
    return si, o


def voisins_o(s, o):
    """Indices des 4 oxygènes liés au silicium s (contrôle : exactement 4)."""
    v = [k for k, q in enumerate(o) if (q - s).length < LIAISON]
    assert len(v) == 4, len(v)
    return v


def voisins_si(q, si):
    return [k for k, s in enumerate(si) if (s - q).length < LIAISON]
