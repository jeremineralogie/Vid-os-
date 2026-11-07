"""Cristaux de quartz réalistes (Cycles) pour « Les couleurs du quartz ».

Prisme hexagonal terminé par une pointe, en verre d'indice 1,544 (celui du quartz), coloré par absorption dans la masse.
Une brume très légère rend visible le faisceau lumineux. La position à l'écran de quelques repères est exportée
(sortie.json) pour placer les étiquettes HyperFrames.

blender -b -P projets/quartz/blender/cristaux.py -- scene sortie.png [largeur hauteur échantillons]
scènes : morion_roche, gamme, amethyste_faisceau, laiteux, laiteux_zoom, transparent
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
SCENE, SORTIE = args[0], args[1]
W, H, ECH = (int(args[2]), int(args[3]), int(args[4])) if len(args) >= 5 else (1080, 1920, 160)

# couleur conservée dans la masse et densité d'absorption (illustratives, proches des teintes réelles)
TEINTES = {
    "clair": ((0.80, 0.72, 0.62), 0.25),
    "fume": ((0.62, 0.46, 0.32), 0.7),
    "morion": ((0.30, 0.22, 0.16), 2.6),
    "amethyste": ((0.66, 0.32, 0.88), 0.55),
    "incolore": ((1.0, 1.0, 1.0), 0.0),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = ECH
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.01
sc.cycles.use_denoising = False  # pas d'OpenImageDenoise ici : débruitage OpenCV après coup
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
sc.cycles.volume_bounces = 8  # diffusion multiple : le quartz laiteux paraît blanc
sc.cycles.caustics_reflective = False
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "Medium High Contrast"

monde = bpy.data.worlds.new("monde")
sc.world = monde
monde.use_nodes = True
nt = monde.node_tree
nt.nodes["Background"].inputs[0].default_value = (0.006, 0.004, 0.01, 1)
brume = nt.nodes.new("ShaderNodeVolumeScatter")
brume.inputs["Density"].default_value = 0.0
nt.links.new(brume.outputs[0], nt.nodes["World Output"].inputs["Volume"])

REPERES = {}
R, HP, HT = 1.0, 3.2, 1.25  # rayon, hauteur du prisme, hauteur de la pointe


def materiau_quartz(teinte, diffusion=0.0):
    couleur, densite = TEINTES[teinte]
    m = bpy.data.materials.new("quartz_" + teinte)
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
    if diffusion > 0:
        # quartz laiteux : la multitude d'inclusions microscopiques diffuse la lumière dans la masse
        dif = t.nodes.new("ShaderNodeVolumeScatter")
        dif.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1)
        dif.inputs["Density"].default_value = diffusion
        t.links.new(dif.outputs[0], t.nodes["Material Output"].inputs["Volume"])
    return m


def cristal(teinte, loc=(0, 0, 0), rot=(-8, 14, 10), echelle=1.0, inclusions=0, graine=4, diffusion=0.0):
    verts, faces = [], []
    for z in (0.0, HP):
        for k in range(6):
            a = math.radians(60 * k + 30)
            verts.append((R * math.cos(a), R * math.sin(a), z))
    verts.append((0.0, 0.0, HP + HT))
    faces.append(tuple(range(5, -1, -1)))
    for k in range(6):
        n = (k + 1) % 6
        faces.append((k, n, 6 + n, 6 + k))
        faces.append((6 + k, 6 + n, 12))
    me = bpy.data.meshes.new("quartz")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("quartz", me)
    sc.collection.objects.link(ob)
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    ob.location = loc
    ob.scale = (echelle,) * 3
    ob.data.materials.append(materiau_quartz(teinte, diffusion))
    biseau = ob.modifiers.new("biseau", "BEVEL")
    biseau.width = 0.03
    biseau.segments = 3
    if inclusions:
        # inclusions fluides : gouttelettes microscopiques qui diffusent la lumière
        random.seed(graine)
        mb = bpy.data.materials.new("inclusion")
        mb.use_nodes = True
        b = mb.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (1, 1, 1, 1)
        b.inputs["Roughness"].default_value = 0.5
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
        modele = bpy.context.object
        modele.data.materials.append(mb)
        for _ in range(inclusions):
            z = random.uniform(0.1, HP + HT * 0.7)
            rmax = R * 0.9 * (1 if z < HP else (1 - (z - HP) / HT))
            a, r = random.uniform(0, 2 * math.pi), rmax * math.sqrt(random.random())
            bulle = modele.copy()
            bulle.parent = ob
            bulle.location = (r * math.cos(a), r * math.sin(a), z)
            bulle.scale = [random.uniform(0.008, 0.028)] * 3
            sc.collection.objects.link(bulle)
        bpy.data.objects.remove(modele)
    return ob


def point(ob, local):
    """Position monde d'un point exprimé dans le repère du cristal."""
    bpy.context.view_layer.update()
    return ob.matrix_world @ Vector(local)


def lampe(type_, loc, energie, taille=1.0, cible=Vector((0, 0, 0)), angle=None):
    bpy.ops.object.light_add(type=type_, location=loc)
    l = bpy.context.object
    l.data.energy = energie
    if type_ == "AREA":
        l.data.size = taille
    if type_ == "SPOT":
        l.data.spot_size = math.radians(angle or 12)
        l.data.spot_blend = 0.25
        l.data.shadow_soft_size = 0.03
    l.rotation_euler = (Vector(cible) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return l


def studio(cible=Vector((0, 0, 0.5)), fort=1.0):
    # petites sources : reflets fins sur les arêtes plutôt que de grands carrés blancs
    lampe("AREA", (-5, -5, 5), 260 * fort, 0.8, cible)
    lampe("AREA", (5, -4, 2.5), 160 * fort, 0.6, cible)
    lampe("AREA", (0, -6, -3), 60 * fort, 1.5, cible)


def fond(force=0.8):
    """Panneau lumineux derrière le sujet (dégradé violet sombre) : il révèle la transparence et la teinte des cristaux."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 7, 0), rotation=(math.radians(90), 0, 0))
    ob = bpy.context.object
    ob.scale = (22, 30, 1)
    mf = bpy.data.materials.new("fond")
    mf.use_nodes = True
    t = mf.node_tree
    t.nodes.remove(t.nodes["Principled BSDF"])
    em = t.nodes.new("ShaderNodeEmission")
    grad = t.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    coord = t.nodes.new("ShaderNodeTexCoord")
    mapping = t.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (-2.0, -1.55, 0)  # halo centré derrière le sujet
    mapping.inputs["Scale"].default_value = (4.0, 3.0, 1)
    t.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
    t.links.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    rampe = t.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = (0.006, 0.004, 0.012, 1)
    rampe.color_ramp.elements[1].color = (0.30, 0.22, 0.40, 1)
    t.links.new(grad.outputs["Fac"], rampe.inputs["Fac"])
    t.links.new(rampe.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = force
    t.links.new(em.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(mf)


def camera(loc, cible, lens=60, decalage=-0.08):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    sc.camera = cam
    cam.rotation_euler = (Vector(cible) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.shift_y = decalage  # le sujet remonte, au-dessus des sous-titres


def faisceau(depart, cible, energie=20000, angle=4):
    brume.inputs["Density"].default_value = 0.004
    lampe("SPOT", depart, energie, cible=cible, angle=angle)


def roche():
    """Bloc de roche granuleuse sous le cristal (sphère bosselée par un bruit)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=3.2, location=(0, 0.4, -4.6))
    ob = bpy.context.object
    ob.scale = (1.5, 1.0, 0.75)
    tex = bpy.data.textures.new("bosses", "CLOUDS")
    tex.noise_scale = 0.6
    d = ob.modifiers.new("bosses", "DISPLACE")
    d.texture = tex
    d.strength = 0.6
    m = bpy.data.materials.new("roche")
    m.use_nodes = True
    t = m.node_tree
    b = t.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.85
    bruit = t.nodes.new("ShaderNodeTexNoise")
    bruit.inputs["Scale"].default_value = 40.0
    rampe = t.nodes.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = (0.012, 0.011, 0.011, 1)
    rampe.color_ramp.elements[1].color = (0.10, 0.09, 0.085, 1)
    t.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])
    t.links.new(rampe.outputs["Color"], b.inputs["Base Color"])
    ob.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return ob


# ---------------------------------------------------------------- scènes
if SCENE == "morion_roche":
    q = cristal("morion", loc=(0, 0, -2.4), rot=(-6, 10, 8))
    roche()
    studio(fort=1.4)
    fond()
    camera((0, -20.0, 0.6), (0, 0, -0.6), lens=55, decalage=-0.04)
    REPERES.update(cristal=point(q, (0, 0, HP * 0.55)), g1=Vector((-3.4, -1.4, -3.0)), g2=Vector((3.3, -1.4, -3.2)),
                   g3=Vector((-1.6, -2.2, -3.5)), g4=Vector((2.0, -2.0, -2.9)))

elif SCENE == "gamme":
    noms = (("clair", -1.85), ("fume", 0.0), ("morion", 1.85))
    for nom, x in noms:
        q = cristal(nom, loc=(x, 0, -2.3), rot=(-6, 4, 12), echelle=0.72)
        REPERES[nom] = point(q, (0, 0, -0.35))
    studio(fort=1.3)
    fond()
    camera((0, -21.0, 0.5), (0, 0, 0.2), lens=55, decalage=-0.2)

elif SCENE in ("amethyste_faisceau", "transparent"):
    teinte = "amethyste" if SCENE == "amethyste_faisceau" else "incolore"
    q = cristal(teinte, loc=(0, 0, -2.4), rot=(-6, 10, 8))
    studio(fort=0.8)
    entree = point(q, (-0.95, 0, 1.7))
    fond()
    camera((0, -19.0, 0.4), (0, 0, 0.6), lens=55, decalage=-0.165)
    REPERES.update(cristal=point(q, (0, 0, 1.7)), entree=entree, sortie=point(q, (0.95, 0, 1.6)))

elif SCENE == "laiteux":
    q = cristal("incolore", loc=(0, 0, -2.4), rot=(-6, 10, 8), diffusion=5.0)
    studio(fort=3.0)
    lampe("AREA", (0, -10, 1.5), 900, 8, Vector((0, 0, 0)))  # grande source frontale : le quartz laiteux renvoie une lumière blanche
    fond()
    camera((0, -19.0, 0.4), (0, 0, 0.6), lens=55, decalage=-0.165)
    REPERES.update(cristal=point(q, (0, 0, 1.6)))

elif SCENE == "laiteux_zoom":
    # gros plan dans le quartz : inclusions fluides biphasées (une goutte de liquide et sa bulle de gaz)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    bloc = bpy.context.object
    bloc.scale = (6, 1.2, 11)
    bloc.data.materials.append(materiau_quartz("incolore", 0.03))
    eau = bpy.data.materials.new("liquide")
    eau.use_nodes = True
    t = eau.node_tree
    t.nodes.remove(t.nodes["Principled BSDF"])
    v = t.nodes.new("ShaderNodeBsdfGlass")
    v.inputs["IOR"].default_value = 1.33 / 1.544  # interface quartz / liquide
    t.links.new(v.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    gaz = bpy.data.materials.new("gaz")
    gaz.use_nodes = True
    t = gaz.node_tree
    t.nodes.remove(t.nodes["Principled BSDF"])
    v = t.nodes.new("ShaderNodeBsdfGlass")
    v.inputs["IOR"].default_value = 1.0 / 1.33  # interface liquide / gaz
    t.links.new(v.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    random.seed(7)
    for k in range(70):
        x, z = random.uniform(-2.6, 2.6), random.uniform(-4.6, 4.6)
        y = random.uniform(-0.4, 0.4)
        r = random.choice((0.05, 0.07, 0.1, 0.14, 0.2, 0.28)) * random.uniform(0.8, 1.2)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, z), segments=48, ring_count=24)
        g = bpy.context.object
        g.scale = (r * random.uniform(1.0, 1.8), r * 0.7, r)
        g.rotation_euler = (0, random.uniform(0, 3.14), 0)
        bpy.ops.object.shade_smooth()
        g.data.materials.append(eau)
        if r > 0.08:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.38, location=(x + r * 0.25, y - r * 0.1, z + r * 0.2), segments=32, ring_count=16)
            bpy.ops.object.shade_smooth()
            bpy.context.object.data.materials.append(gaz)
        if k == 0:
            REPERES["inclusion"] = Vector((x, y, z))
    # une inclusion bien visible, près du centre, pour l'étiquette
    x, y, z = 0.6, 0.0, 1.2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, z), segments=64, ring_count=32)
    g = bpy.context.object
    g.scale = (0.62, 0.3, 0.42)
    bpy.ops.object.shade_smooth()
    g.data.materials.append(eau)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(x + 0.2, y - 0.05, z + 0.1), segments=48, ring_count=24)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(gaz)
    REPERES.update(inclusion=Vector((x, y, z)), bulle=Vector((x + 0.2, y - 0.05, z + 0.1)))
    lampe("AREA", (-4, -6, 5), 300, 1.0, Vector((0, 0, 0)))
    fond(0.9)
    camera((0, -9.0, 0.6), (0, 0, 0.6), lens=50, decalage=-0.05)

else:
    raise SystemExit("scène inconnue : " + SCENE)

bpy.context.view_layer.update()
ecran = {}
for nom, p in REPERES.items():
    u = world_to_camera_view(sc, sc.camera, p)
    ecran[nom] = [round(u.x * W, 1), round((1 - u.y) * H, 1)]
Path(SORTIE).with_suffix(".json").write_text(json.dumps(ecran))
sc.render.filepath = SORTIE
bpy.ops.render.render(write_still=True)
print("rendu", SCENE, SORTIE)
