"""Cristal de quartz réaliste (Cycles) : prisme hexagonal terminé par une pointe, en verre d'indice 1,544,
coloré par absorption dans la masse ; faisceau lumineux visible (brume légère) et inclusions possibles.

blender -b -P projets/quartz/blender/cristal.py -- sortie.png variete [largeur hauteur échantillons]
variete : morion, fume, amethyste, laiteux, transparent
"""
import math
import random
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
SORTIE, VARIETE = args[0], args[1]
W, H, ECH = (int(args[2]), int(args[3]), int(args[4])) if len(args) >= 5 else (1080, 1920, 128)

# couleur absorbée dans la masse (ce qui reste est la couleur vue), densité d'absorption, inclusions
VARIETES = {
    "morion": ((0.30, 0.22, 0.16), 2.2, 0),
    "fume": ((0.62, 0.46, 0.32), 0.45, 0),
    "amethyste": ((0.62, 0.30, 0.85), 0.40, 0),
    "laiteux": ((0.95, 0.95, 0.96), 0.0, 900),
    "transparent": ((1.0, 1.0, 1.0), 0.0, 0),
}
couleur, densite, n_inclusions = VARIETES[VARIETE]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = ECH
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
sc.cycles.volume_bounces = 2
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "Medium High Contrast"

# monde sombre avec une brume légère pour rendre le faisceau visible
monde = bpy.data.worlds.new("monde")
sc.world = monde
monde.use_nodes = True
nt = monde.node_tree
nt.nodes["Background"].inputs[0].default_value = (0.006, 0.004, 0.01, 1)
brume = nt.nodes.new("ShaderNodeVolumeScatter")
brume.inputs["Density"].default_value = 0.0035
nt.links.new(brume.outputs[0], nt.nodes["World Output"].inputs["Volume"])

# ---------------------------------------------------------------- le cristal
R, HP, HT = 1.0, 3.2, 1.25  # rayon, hauteur du prisme, hauteur de la pointe
verts, faces = [], []
for k in range(6):
    a = math.radians(60 * k + 30)
    verts.append((R * math.cos(a), R * math.sin(a), 0.0))
for k in range(6):
    a = math.radians(60 * k + 30)
    verts.append((R * math.cos(a), R * math.sin(a), HP))
verts.append((0.0, 0.0, HP + HT))
faces.append(tuple(range(5, -1, -1)))
for k in range(6):
    n = (k + 1) % 6
    faces.append((k, n, 6 + n, 6 + k))
    faces.append((6 + k, 6 + n, 12))
me = bpy.data.meshes.new("quartz")
me.from_pydata(verts, [], faces)
cristal = bpy.data.objects.new("quartz", me)
sc.collection.objects.link(cristal)
cristal.rotation_euler = (math.radians(-8), math.radians(14), math.radians(10))
cristal.location = (0, 0, -2.2)

m = bpy.data.materials.new("quartz")
m.use_nodes = True
t = m.node_tree
t.nodes.remove(t.nodes["Principled BSDF"])
verre = t.nodes.new("ShaderNodeBsdfGlass")
verre.inputs["IOR"].default_value = 1.544
verre.inputs["Roughness"].default_value = 0.02
t.links.new(verre.outputs[0], t.nodes["Material Output"].inputs["Surface"])
if densite > 0:
    absorb = t.nodes.new("ShaderNodeVolumeAbsorption")
    absorb.inputs["Color"].default_value = (*couleur, 1)
    absorb.inputs["Density"].default_value = densite
    t.links.new(absorb.outputs[0], t.nodes["Material Output"].inputs["Volume"])
cristal.data.materials.append(m)
biseau = cristal.modifiers.new("biseau", "BEVEL")
biseau.width = 0.035
biseau.segments = 3
cristal.data.shade_flat() if hasattr(cristal.data, "shade_flat") else None

# inclusions fluides : petites bulles (gouttelette + bulle de gaz) qui diffusent la lumière
if n_inclusions:
    random.seed(4)
    mb = bpy.data.materials.new("inclusion")
    mb.use_nodes = True
    b = mb.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 1, 1, 1)
    b.inputs["Roughness"].default_value = 0.6
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
    modele = bpy.context.object
    modele.data.materials.append(mb)
    for _ in range(n_inclusions):
        z = random.uniform(0.15, HP + HT * 0.6)
        rmax = R * 0.85 * (1 if z < HP else (1 - (z - HP) / HT))
        a, r = random.uniform(0, 2 * math.pi), rmax * math.sqrt(random.random())
        bulle = modele.copy()
        bulle.data = modele.data
        bulle.parent = cristal
        bulle.location = (r * math.cos(a), r * math.sin(a), z)
        bulle.scale = [random.uniform(0.012, 0.035)] * 3
        sc.collection.objects.link(bulle)
    bpy.data.objects.remove(modele)

# ---------------------------------------------------------------- lumières
def lampe(type_, loc, energie, taille=1.0, cible=Vector((0, 0, 0)), angle=None):
    bpy.ops.object.light_add(type=type_, location=loc)
    l = bpy.context.object
    l.data.energy = energie
    if type_ == "AREA":
        l.data.size = taille
    if type_ == "SPOT":
        l.data.spot_size = math.radians(angle or 12)
        l.data.spot_blend = 0.3
        l.data.shadow_soft_size = 0.05
    l.rotation_euler = (cible - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return l


lampe("AREA", (0.5, 5, 1.5), 900, 3, cible=Vector((0, 0, 0.5)))        # contre-jour : la lumière traverse le cristal
lampe("AREA", (-6, -4, 4), 500, 5, cible=Vector((0, 0, 0.5)))          # boîte à lumière, reflets sur les faces
lampe("AREA", (6, -5, 2), 350, 2, cible=Vector((0, 0, 0.5)))           # liseré
lampe("SPOT", (-8, 1.5, 1.0), 20000, cible=Vector((0, 0, 0.6)), angle=5)  # faisceau visible

# fond : panneau sombre dégradé derrière le cristal
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 9, 0), rotation=(math.radians(90), 0, 0))
mf = bpy.data.materials.new("fond")
mf.use_nodes = True
mf.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.02, 0.045, 1)
mf.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
bpy.context.object.data.materials.append(mf)

bpy.ops.object.camera_add(location=(0.0, -11.0, 0.6))
cam = bpy.context.object
sc.camera = cam
cam.rotation_euler = (Vector((0, 0, 0.1)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 60

sc.render.filepath = SORTIE
bpy.ops.render.render(write_still=True)
print("rendu", SORTIE, VARIETE)
