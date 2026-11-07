"""Scènes réalistes (modèle 3D) de « Les couleurs du quartz », rendues avec Cycles.

blender -b -P projets/quartz/blender/scenes.py -- scene sortie.png [largeur hauteur échantillons]

Scènes :
  tetraedre   un tétraèdre SiO4 isolé, en gros plan
  reseau      le réseau du quartz α en tétraèdres, vu dans l'axe c (canaux hexagonaux)
  al_avant    centre aluminium avant irradiation : Al³⁺ à la place d'un Si⁴⁺, H⁺ compensateur lié à un O voisin
  al_apres    après irradiation : H⁺ parti, un électron arraché à un O voisin de Al → « trou » sur cet O ([AlO4]⁰)
Les deux scènes « al » ont le même cadrage, pour passer de l'une à l'autre en fondu.
"""
import math
import sys
from pathlib import Path

import json

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quartz_alpha import C, LIAISON, reseau, voisins_o, voisins_si  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
SCENE, SORTIE = args[0], args[1]
W, H, ECH = (int(args[2]), int(args[3]), int(args[4])) if len(args) >= 5 else (1080, 1920, 256)

# ---------------------------------------------------------------- réglages communs
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = ECH
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.006
sc.cycles.use_denoising = False  # Blender de la distribution : pas d'OpenImageDenoise
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "Medium High Contrast"
monde = bpy.data.worlds.new("monde")
sc.world = monde
monde.use_nodes = True
monde.node_tree.nodes["Background"].inputs[0].default_value = (0.010, 0.006, 0.016, 1)


def matiere(nom, rgb, rugo=0.25, metal=0.0, emission=None, force=0.0, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rugo
    b.inputs["Metallic"].default_value = metal
    for n in ("Coat Weight", "Clearcoat"):
        if n in b.inputs:
            b.inputs[n].default_value = 0.5
    if emission:
        for n in ("Emission Color", "Emission"):
            if n in b.inputs:
                b.inputs[n].default_value = (*emission, 1)
                break
        b.inputs["Emission Strength"].default_value = force
    if transmission:
        for n in ("Transmission Weight", "Transmission"):
            if n in b.inputs:
                b.inputs[n].default_value = transmission
    b.inputs["Alpha"].default_value = alpha
    return m


M = {
    "si": matiere("Si", (0.42, 0.22, 0.88), 0.22),
    "o": matiere("O", (0.80, 0.14, 0.16), 0.25),
    "liaison": matiere("liaison", (0.80, 0.78, 0.84), 0.35),
    "al": matiere("Al", (0.95, 0.68, 0.22), 0.25, metal=0.3),
    "h": matiere("H", (0.92, 0.95, 1.0), 0.2),
    "trou": matiere("trou", (1.0, 0.55, 0.15), 0.3, emission=(1.0, 0.55, 0.15), force=2.0),
    "fe": matiere("Fe", (0.72, 0.42, 0.30), 0.3, metal=0.4),
    "fe_apres": matiere("Fe4", (0.80, 0.45, 1.0), 0.3, emission=(0.75, 0.35, 1.0), force=2.0),
    "tetra": matiere("tetra", (0.50, 0.30, 0.95), 0.15, transmission=0.55, alpha=0.85),
}


def sphere(p, r, m, seg=64):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p, segments=seg, ring_count=seg // 2)
    ob = bpy.context.object
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob


def baton(a, b, r, m):
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=32)
    ob = bpy.context.object
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)


def tetraedre(pts, m):
    me = bpy.data.meshes.new("t")
    c = sum(pts, Vector()) / 4
    faces = []
    for f in ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)):
        n = (pts[f[1]] - pts[f[0]]).cross(pts[f[2]] - pts[f[0]])
        faces.append(f if n.dot(pts[f[0]] - c) > 0 else (f[0], f[2], f[1]))  # normales vers l'extérieur
    me.from_pydata([tuple(p) for p in pts], [], faces)
    ob = bpy.data.objects.new("t", me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(m)


def lampe(loc, energie, taille, cible):
    bpy.ops.object.light_add(type="AREA", location=loc)
    l = bpy.context.object
    l.data.energy = energie
    l.data.size = taille
    l.rotation_euler = (cible - l.location).to_track_quat("-Z", "Y").to_euler()


def camera(loc, cible, lens=50, ortho=None, flou=None, decalage=-0.11):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    sc.camera = cam
    cam.rotation_euler = (cible - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.shift_y = decalage  # le sujet remonte vers y ≈ 750, au-dessus des sous-titres
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    if flou:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = (cible - cam.location).length
        cam.data.dof.aperture_fstop = flou


def eclairage(cible, d=30):
    lampe(cible + Vector((d * 0.6, -d * 0.6, d)), 6000, d * 0.4, cible)
    lampe(cible + Vector((-d * 0.8, d * 0.3, d * 0.6)), 2500, d * 0.5, cible)
    lampe(cible + Vector((0, d, -d * 0.3)), 3500, d * 0.3, cible)


SI, O = reseau((6, 6, 2))
REPERES = {}  # points dont la position à l'écran est exportée (pour les étiquettes HyperFrames)

# ---------------------------------------------------------------- scènes
if SCENE == "tetraedre":
    s = min(SI, key=lambda p: (p - Vector((7.5, 6.5, 2.7))).length)
    for k in voisins_o(s, O):
        baton(s, O[k], 0.15, M["liaison"])
        sphere(O[k], 0.62, M["o"])
    sphere(s, 0.48, M["si"])
    eclairage(s, 12)
    # vue choisie pour voir les quatre oxygènes : direction moyenne décalée hors des liaisons
    v = [(O[k] - s).normalized() for k in voisins_o(s, O)]
    regard = (v[0] - v[1] + v[2] * 0.3).normalized()
    camera(s + regard * 15.0 + Vector((0, 0, 1.5)), s, lens=50, decalage=-0.06)
    REPERES.update(si=s, **{f"o{n}": O[k] for n, k in enumerate(voisins_o(s, O))})

elif SCENE == "reseau":
    centre = Vector((sum(p.x for p in SI) / len(SI), sum(p.y for p in SI) / len(SI), 0.75 * C))
    rayon = 12.5
    garde = [p for p in SI if Vector((p.x - centre.x, p.y - centre.y)).length < rayon and -0.1 < p.z < 1.5 * C]
    o_gardes = set()
    for s in garde:
        v = voisins_o(s, O)
        tetraedre([O[k] for k in v], M["tetra"])
        o_gardes.update(v)
    for k in o_gardes:
        sphere(O[k], 0.32, M["o"], 32)
    for s in garde:
        sphere(s, 0.22, M["si"], 32)
    eclairage(centre, 40)
    camera(centre + Vector((0.0, -6.0, 60.0)), centre, ortho=2 * rayon * 1.02, decalage=0.0)
    REPERES.update(centre=centre)

elif SCENE in ("al_avant", "al_apres", "fe_avant", "fe_apres"):
    # Al : un oxygène voisin perd un électron (centre [AlO4]⁰, quartz fumé et morion).
    # Fe : l'ion de fer lui-même perd un électron (Fe³⁺ → Fe⁴⁺, améthyste) ; pas d'hydrogène représenté.
    fer = SCENE.startswith("fe")
    apres = SCENE.endswith("apres")
    # un amas de tétraèdres autour d'un silicium central, que l'on remplace par l'aluminium
    al = min(SI, key=lambda p: (p - Vector((7.5, 6.5, 2.7))).length)
    o_al = voisins_o(al, O)
    si_amas = {SI.index(al)}
    for k in o_al:
        si_amas.update(voisins_si(O[k], SI))
    o_amas = set()
    for i in si_amas:
        o_amas.update(voisins_o(SI[i], O))
    o_final = set()
    for i in si_amas:
        o_final.update(voisins_o(SI[i], O))
    o_trou = o_al[0]  # l'oxygène voisin de Al qui perd un électron (le « trou »)
    dopant = M["fe"] if fer else M["al"]
    # H⁺ compensateur : lié à un O voisin de Al (liaison O–H d'environ 1 Å), pointant hors des liaisons Si
    o_h = o_al[0]
    si_lies = [SI[i] for i in voisins_si(O[o_h], SI)]
    direction = (O[o_h] * 2 - si_lies[0] - si_lies[1]).normalized()
    h = O[o_h] + direction * 1.0
    for i in si_amas:
        s = SI[i]
        for k in voisins_o(s, O):
            baton(s, O[k], 0.13, M["liaison"])
    for k in o_final:
        m = M["trou"] if (apres and not fer and k == o_trou) else M["o"]
        sphere(O[k], 0.40 if k in o_al else 0.34, m)
    for i in si_amas:
        sphere(SI[i], 0.46 if SI[i] is al else 0.30, (M["fe_apres"] if (fer and apres) else dopant) if SI[i] is al else M["si"])
    if fer:
        pass
    elif not apres:
        baton(O[o_h], h, 0.08, M["liaison"])
        sphere(h, 0.22, M["h"])
    else:
        # lueur autour de l'oxygène qui a perdu son électron
        halo = bpy.data.materials.new("halo")
        halo.use_nodes = True
        t = halo.node_tree
        t.nodes.remove(t.nodes["Principled BSDF"])
        mix = t.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 0.22
        t.links.new(t.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
        em = t.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1.0, 0.55, 0.15, 1)
        em.inputs["Strength"].default_value = 0.7
        t.links.new(em.outputs[0], mix.inputs[2])
        t.links.new(mix.outputs[0], t.nodes["Material Output"].inputs["Surface"])
        sphere(O[o_trou], 0.50, halo, 48)
    if fer and apres:
        halo = bpy.data.materials.new("halo_fe")
        halo.use_nodes = True
        t = halo.node_tree
        t.nodes.remove(t.nodes["Principled BSDF"])
        mix = t.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 0.22
        t.links.new(t.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
        em = t.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.75, 0.35, 1.0, 1)
        em.inputs["Strength"].default_value = 0.8
        t.links.new(em.outputs[0], mix.inputs[2])
        t.links.new(mix.outputs[0], t.nodes["Material Output"].inputs["Surface"])
        sphere(al, 0.62, halo, 48)
    eclairage(al, 18)
    # caméra du côté de l'oxygène concerné, pour qu'il soit au premier plan avec Al et H
    v = (O[o_trou] - al).normalized()
    lat = v.cross(Vector((0, 0, 1))).normalized()
    camera(al + v * 19.0 + lat * 5.0 + Vector((0, 0, 3.5)), (al + O[o_trou]) / 2, lens=50, decalage=-0.07)
    REPERES.update(al=al, trou=O[o_trou], h=h)

else:
    raise SystemExit("scène inconnue : " + SCENE)

bpy.context.view_layer.update()  # matrices de la caméra à jour avant la projection
ecran = {}
for nom, p in REPERES.items():
    u = world_to_camera_view(sc, sc.camera, p)
    ecran[nom] = [round(u.x * W, 1), round((1 - u.y) * H, 1)]
Path(SORTIE).with_suffix(".json").write_text(json.dumps(ecran))

sc.render.filepath = SORTIE
bpy.ops.render.render(write_still=True)
print("rendu", SCENE, SORTIE)
