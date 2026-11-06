"""Structure réelle du quartz α (rendu Blender, Cycles) : boules et bâtonnets, plusieurs mailles.

Données cristallographiques du quartz α (groupe d'espace P3₂21) :
a = 4,9134 Å, c = 5,4052 Å ; Si en 3a (x = 0,4697) ; O en 6c (0,4135 ; 0,2669 ; 0,1191).
Liaisons Si–O retenues sous 1,7 Å (valeur mesurée : environ 1,61 Å).

blender -b -P projets/quartz/blender/structure.py -- sortie.png [largeur hauteur échantillons]
"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SORTIE = args[0] if args else "/tmp/structure.png"
W, H, ECH = (int(args[1]), int(args[2]), int(args[3])) if len(args) >= 4 else (1080, 1920, 64)
STYLE = args[4] if len(args) >= 5 else "tetraedres"  # « tetraedres » (polyèdres SiO4) ou « boules »

A, C = 4.9134, 5.4052
OPS = [lambda x, y, z: (x, y, z), lambda x, y, z: (-y, x - y, z + 2 / 3), lambda x, y, z: (-x + y, -x, z + 1 / 3),
       lambda x, y, z: (y, x, -z + 2 / 3), lambda x, y, z: (x - y, -y, -z), lambda x, y, z: (-x, -x + y, -z + 1 / 3)]
# (vérifié : chaque Si a 4 O à 1,604 et 1,613 Å, chaque O est lié à 2 Si)


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


SI = orbite((0.4697, 0.0, 0.0))
O = orbite((0.4135, 0.2669, 0.1191))
assert len(SI) == 3 and len(O) == 6, (len(SI), len(O))

N = (6, 6, 2)  # mailles répétées
atomes_si, atomes_o = [], []
for i in range(-1, N[0] + 1):
    for j in range(-1, N[1] + 1):
        for k in range(-1, N[2] + 1):
            for f in SI:
                atomes_si.append(cart((f[0] + i, f[1] + j, f[2] + k)))
            for f in O:
                atomes_o.append(cart((f[0] + i, f[1] + j, f[2] + k)))

# on garde un cylindre d'axe c (une hauteur de maille et demie), puis les oxygènes liés aux silicium gardés
centre = cart((N[0] / 2, N[1] / 2, 0.5))
rayon = 12.5
si = [p for p in atomes_si if Vector((p.x - centre.x, p.y - centre.y)).length < rayon and -0.1 < p.z < 1.5 * C]
liaisons, o_gardes, tetraedres = [], set(), []
for s in si:
    voisins = [(idx, q) for idx, q in enumerate(atomes_o) if (q - s).length < 1.7]
    assert len(voisins) == 4, len(voisins)  # chaque silicium : 4 oxygènes
    for idx, q in voisins:
        liaisons.append((s, q))
        o_gardes.add(idx)
    tetraedres.append([q for _, q in voisins])
o = [atomes_o[i] for i in o_gardes]

# ---------------------------------------------------------------- scène
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = ECH
sc.cycles.use_denoising = False  # Blender de la distribution : pas d'OpenImageDenoise"'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX" if "AgX" in [v.identifier for v in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "Filmic"

monde = bpy.data.worlds.new("monde")
sc.world = monde
monde.use_nodes = True
fond = monde.node_tree.nodes["Background"]
fond.inputs[0].default_value = (0.012, 0.007, 0.02, 1)
fond.inputs[1].default_value = 1.0


def matiere(nom, rgb, rugo=0.25, emission=0.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rugo
    for nom_in in ("Coat Weight", "Clearcoat"):
        if nom_in in b.inputs:
            b.inputs[nom_in].default_value = 0.6
    return m


m_si = matiere("Si", (0.42, 0.20, 0.85))
m_o = matiere("O", (0.85, 0.16, 0.18))
m_l = matiere("liaison", (0.78, 0.76, 0.82), 0.35)


def sphere(p, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p, segments=48, ring_count=24)
    ob = bpy.context.object
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)


def baton(a, b, r, m):
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=24)
    ob = bpy.context.object
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)


def tetraedre(pts, m):
    me = bpy.data.meshes.new("t")
    me.from_pydata([tuple(p) for p in pts], [], [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    me.normals_split_custom_set_from_vertices if False else None
    ob = bpy.data.objects.new("t", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.select_set(False)


if STYLE == "boules":
    for p in si:
        sphere(p, 0.42, m_si)
    for p in o:
        sphere(p, 0.55, m_o)
    for a, b in liaisons:
        baton(a, b, 0.13, m_l)
else:
    m_t = bpy.data.materials.new("tetra")
    m_t.use_nodes = True
    b = m_t.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.50, 0.30, 0.95, 1)
    b.inputs["Roughness"].default_value = 0.15
    for nom_in in ("Transmission Weight", "Transmission"):
        if nom_in in b.inputs:
            b.inputs[nom_in].default_value = 0.55
    b.inputs["Alpha"].default_value = 0.85
    for pts in tetraedres:
        tetraedre(pts, m_t)
    for p in o:
        sphere(p, 0.32, m_o)
    for p in si:
        sphere(p, 0.22, m_si)

# caméra orthographique dans l'axe c, à peine inclinée : on voit les canaux hexagonaux du quartz
cible = centre + Vector((0, 0, 0.75 * C))
bpy.ops.object.camera_add(location=cible + Vector((0.0, -6.0, 60.0)))
cam = bpy.context.object
sc.camera = cam
direction = cible - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2 * rayon * 1.05 * max(1, H / W)

for loc, energie, taille in (((20, -20, 40), 4000, 12), ((-25, 15, 20), 1500, 14), ((0, 30, -10), 2500, 8)):
    bpy.ops.object.light_add(type="AREA", location=cible + Vector(loc))
    l = bpy.context.object
    l.data.energy = energie
    l.data.size = taille
    l.rotation_euler = (cible - l.location).to_track_quat("-Z", "Y").to_euler()

sc.render.filepath = SORTIE
bpy.ops.render.render(write_still=True)
print("rendu", SORTIE, len(si), "Si", len(o), "O", len(liaisons), "liaisons")
