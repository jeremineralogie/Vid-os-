"""Bibliothèque commune : matériaux (roche, fluorite, fluide), géométrie procédurale, rendu Eevee.

Fluorite : CaF2, système cubique, indice de réfraction 1,434. Les cristaux sont des cubes aux arêtes vives
(chanfrein très fin), avec un cœur plus violet (zonation : « fantôme » cubique concentrique).
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

FPS = 30
W, H = 1080, 1920


def hexa(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):
    """sRGB -> linéaire, avec alpha."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in hexa(c)) + (1.0,)


def vider():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def scene_base(fin, fond="#08080C", ssr=True, volumes=False, echantillons=24):
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = W, H
    s.render.resolution_percentage = 100
    s.render.fps = FPS
    s.frame_start, s.frame_end = 1, fin
    e = s.eevee
    e.taa_render_samples = echantillons
    e.use_gtao = True
    e.gtao_distance = 0.4
    e.use_soft_shadows = True
    e.shadow_cube_size = "1024"
    e.shadow_cascade_size = "2048"
    e.use_bloom = True
    e.bloom_threshold = 1.2
    e.bloom_intensity = 0.03
    e.bloom_radius = 5
    e.use_ssr = ssr
    e.use_ssr_refraction = ssr
    e.ssr_quality = 0.5
    e.ssr_thickness = 0.05
    e.use_volumetric_lights = volumes
    e.volumetric_tile_size = "8"
    e.volumetric_samples = 48
    e.volumetric_end = 30
    s.view_settings.view_transform = "Filmic"
    s.view_settings.look = "Medium High Contrast"
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    monde = bpy.data.worlds.new("monde")
    s.world = monde
    monde.use_nodes = True
    bg = monde.node_tree.nodes["Background"]
    bg.inputs[0].default_value = lin(fond)
    bg.inputs[1].default_value = 1.0
    return s


def brume(densite=0.015, couleur="#B49AEF", anisotropie=0.4):
    """Volume de diffusion dans le monde (rayons de lumière visibles)."""
    nt = bpy.context.scene.world.node_tree
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = densite
    v.inputs["Color"].default_value = lin(couleur)
    v.inputs["Anisotropy"].default_value = anisotropie
    nt.links.new(v.outputs[0], nt.nodes["World Output"].inputs["Volume"])


# ---------------------------------------------------------------- matériaux

ALIAS = {"Specular": "Specular IOR Level", "Transmission": "Transmission Weight", "Subsurface": "Subsurface Weight",
         "Emission": "Emission Color"}


def entree(p, nom):
    return p.inputs[nom] if nom in p.inputs else p.inputs[ALIAS[nom]]


def _n(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        if k == "use_clamp":
            n.use_clamp = v
        elif k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def mat_roche(nom="roche", clair="#5E5961", sombre="#1C1A20", echelle=3.0, relief=0.6, veine=None):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    coord = _n(nt, "ShaderNodeTexCoord")
    bruit = _n(nt, "ShaderNodeTexNoise", Scale=echelle, Detail=12.0, Roughness=0.62)
    nt.links.new(coord.outputs["Object"], bruit.inputs["Vector"])
    vor = _n(nt, "ShaderNodeTexVoronoi", Scale=echelle * 7)
    nt.links.new(coord.outputs["Object"], vor.inputs["Vector"])
    rampe = _n(nt, "ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].position = 0.32
    rampe.color_ramp.elements[0].color = lin(sombre)
    rampe.color_ramp.elements[1].position = 0.72
    rampe.color_ramp.elements[1].color = lin(clair)
    # grains clairs (feldspath/quartz) et sombres, à petite échelle
    grains = _n(nt, "ShaderNodeMixRGB", blend_type="MULTIPLY")
    grains.inputs["Fac"].default_value = 0.35
    nt.links.new(bruit.outputs["Fac"], rampe.inputs["Fac"])
    nt.links.new(rampe.outputs["Color"], grains.inputs["Color1"])
    gris = _n(nt, "ShaderNodeMapRange")
    gris.inputs["From Min"].default_value = 0.0
    gris.inputs["From Max"].default_value = 0.6
    gris.inputs["To Min"].default_value = 0.55
    gris.inputs["To Max"].default_value = 1.0
    nt.links.new(vor.outputs["Distance"], gris.inputs["Value"])
    nt.links.new(gris.outputs["Result"], grains.inputs["Color2"])
    nt.links.new(grains.outputs["Color"], p.inputs["Base Color"])
    rough = _n(nt, "ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.62
    rough.inputs["To Max"].default_value = 0.95
    nt.links.new(bruit.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], p.inputs["Roughness"])
    bosse = _n(nt, "ShaderNodeBump", Strength=relief, Distance=0.05)
    fin = _n(nt, "ShaderNodeTexNoise", Scale=echelle * 25, Detail=8.0)
    nt.links.new(coord.outputs["Object"], fin.inputs["Vector"])
    somme = _n(nt, "ShaderNodeMath", operation="ADD")
    nt.links.new(fin.outputs["Fac"], somme.inputs[0])
    nt.links.new(vor.outputs["Distance"], somme.inputs[1])
    nt.links.new(somme.outputs[0], bosse.inputs["Height"])
    nt.links.new(bosse.outputs["Normal"], p.inputs["Normal"])
    entree(p, "Specular").default_value = 0.35
    return m


def mat_fluorite(nom="fluorite", couleur="#7650C9", rugosite=0.02, lueur=0.25, opacite=0.45):
    """Fluorite violette transparente.

    Eevee (rendu logiciel) : transparence teintée + reflet brillant pondéré par Fresnel (IOR 1,434),
    plus une faible lueur interne qui suit l'épaisseur traversée (plus dense au centre des faces).
    On voit au travers le cœur plus coloré du cristal : la zonation de croissance.
    """
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    sortie = nt.nodes["Material Output"]
    teinte = lin(couleur)
    clair = tuple(0.35 + 0.65 * c for c in teinte[:3]) + (1.0,)
    transp = _n(nt, "ShaderNodeBsdfTransparent")
    transp.inputs["Color"].default_value = clair
    brillant = _n(nt, "ShaderNodeBsdfPrincipled")
    brillant.inputs["Base Color"].default_value = teinte
    brillant.inputs["Roughness"].default_value = rugosite
    entree(brillant, "Specular").default_value = 1.0
    brillant.inputs["Coat Weight"].default_value = 0.6
    brillant.inputs["Coat Roughness"].default_value = 0.005
    # micro-relief des faces (figures de croissance, très discret)
    coord = _n(nt, "ShaderNodeTexCoord")
    b = _n(nt, "ShaderNodeTexNoise", Scale=7.0, Detail=3.0)
    nt.links.new(coord.outputs["Object"], b.inputs["Vector"])
    bosse = _n(nt, "ShaderNodeBump", Strength=0.025, Distance=0.02)
    nt.links.new(b.outputs["Fac"], bosse.inputs["Height"])
    nt.links.new(bosse.outputs["Normal"], brillant.inputs["Normal"])
    nt.links.new(bosse.outputs["Normal"], brillant.inputs["Coat Normal"])
    lw = _n(nt, "ShaderNodeLayerWeight", Blend=0.18)
    nt.links.new(bosse.outputs["Normal"], lw.inputs["Normal"])
    fac = _n(nt, "ShaderNodeMath", operation="ADD", use_clamp=True)
    fac.inputs[1].default_value = opacite
    nt.links.new(lw.outputs["Fresnel"], fac.inputs[0])
    mix = _n(nt, "ShaderNodeMixShader")
    nt.links.new(fac.outputs[0], mix.inputs[0])
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(brillant.outputs[0], mix.inputs[2])
    # lueur interne (lumière transmise), plus forte face à l'observateur
    em = _n(nt, "ShaderNodeEmission", Strength=lueur)
    em.inputs["Color"].default_value = teinte
    ajout = _n(nt, "ShaderNodeAddShader")
    nt.links.new(mix.outputs[0], ajout.inputs[0])
    nt.links.new(em.outputs[0], ajout.inputs[1])
    nt.links.new(ajout.outputs[0], sortie.inputs["Surface"])
    m.blend_method = "BLEND"
    m.shadow_method = "HASHED"
    m.show_transparent_back = False
    m.use_backface_culling = False
    return m


def mat_coeur(nom="coeur", couleur="#3A1E78", emission=0.0):
    """Zone interne plus colorée (zonation), vue au travers de l'enveloppe."""
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(couleur)
    p.inputs["Roughness"].default_value = 0.25
    entree(p, "Subsurface").default_value = 0.3
    p.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.6)
    if emission:
        entree(p, "Emission").default_value = lin("#7650C9")
        p.inputs["Emission Strength"].default_value = emission
    return m


def mat_emission(nom, couleur, force):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = _n(nt, "ShaderNodeEmission", Strength=force)
    e.inputs["Color"].default_value = lin(couleur)
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def mat_fluide(nom="fluide", couleur="#D6A875", densite=0.6, force=0.4):
    """Fluide hydrothermal : volume translucide légèrement lumineux (eau chaude), pas de lave."""
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = _n(nt, "ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = lin("#E6E6F0")
    v.inputs["Emission Color"].default_value = lin(couleur)
    coord = _n(nt, "ShaderNodeTexCoord")
    mp = _n(nt, "ShaderNodeMapping")
    nt.links.new(coord.outputs["Object"], mp.inputs["Vector"])
    b = _n(nt, "ShaderNodeTexNoise", Scale=2.2, Detail=3.0)
    nt.links.new(mp.outputs["Vector"], b.inputs["Vector"])
    r = _n(nt, "ShaderNodeMapRange")
    r.inputs["From Min"].default_value = 0.45
    r.inputs["From Max"].default_value = 0.75
    r.inputs["To Min"].default_value = 0.0
    r.inputs["To Max"].default_value = densite
    nt.links.new(b.outputs["Fac"], r.inputs["Value"])
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    masque = None
    for axe in ("X", "Y", "Z"):
        ab = _n(nt, "ShaderNodeMath", operation="ABSOLUTE")
        nt.links.new(sep.outputs[axe], ab.inputs[0])
        bord = _n(nt, "ShaderNodeMapRange")
        bord.inputs["From Min"].default_value = 0.5
        bord.inputs["From Max"].default_value = 0.36 if axe == "Y" else 0.3
        nt.links.new(ab.outputs[0], bord.inputs["Value"])
        if masque is None:
            masque = bord
        else:
            mul = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
            nt.links.new(masque.outputs[0], mul.inputs[0])
            nt.links.new(bord.outputs[0], mul.inputs[1])
            masque = mul
    dens = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(r.outputs["Result"], dens.inputs[0])
    nt.links.new(masque.outputs[0], dens.inputs[1])
    nt.links.new(dens.outputs[0], v.inputs["Density"])
    em = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
    em.inputs[1].default_value = force
    nt.links.new(dens.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], v.inputs["Emission Strength"])
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m, mp


# ---------------------------------------------------------------- géométrie

def objet(nom, me, mat=None):
    o = bpy.data.objects.new(nom, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def lisser(o):
    for p in o.data.polygons:
        p.use_smooth = True


def roche_brute(nom="caillou", rayon=1.0, graine=3, subdiv=6, mat=None):
    """Bloc irrégulier : icosphère aplatie, bruit fractal, fractures (plans de coupe adoucis)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=rayon)
    rng = random.Random(graine)
    plans = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(), rng.uniform(0.55, 0.8))
             for _ in range(4)]
    dec = Vector((graine * 3.1, graine * 1.7, graine * 0.9))
    for v in bm.verts:
        p = v.co.copy()
        p.x *= 1.25
        p.z *= 0.78
        d = noise.fractal(p * 1.3 + dec, 0.55, 2.1, 6)
        p *= 1 + 0.28 * d
        p += p.normalized() * 0.03 * noise.noise(p * 9 + dec)
        for n, dist in plans:  # faces de cassure : on rabote ce qui dépasse
            h = p.dot(n) - dist * rayon
            if h > 0:
                p -= n * h * 0.7
        v.co = p
    me = bpy.data.meshes.new(nom)
    bm.to_mesh(me)
    bm.free()
    o = objet(nom, me, mat)
    lisser(o)
    return o


def cube_cristal(nom, taille, mat, chanfrein=0.012):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(nom)
    bm.to_mesh(me)
    bm.free()
    o = objet(nom, me, mat)
    mo = o.modifiers.new("chanfrein", "BEVEL")
    mo.width = chanfrein
    mo.segments = 2
    mo.limit_method = "NONE"
    mo.harden_normals = True
    o.data.use_auto_smooth = True
    lisser(o)
    o.scale = (taille,) * 3
    return o


def camera(nom="cam", focale=35, ouverture=None, mise_au_point=None):
    c = bpy.data.cameras.new(nom)
    c.lens = focale
    c.sensor_width = 36
    c.clip_start = 0.01
    c.clip_end = 200
    o = bpy.data.objects.new(nom, c)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    if ouverture:
        c.dof.use_dof = True
        c.dof.aperture_fstop = ouverture
        if isinstance(mise_au_point, bpy.types.Object):
            c.dof.focus_object = mise_au_point
        elif mise_au_point:
            c.dof.focus_distance = mise_au_point
    return o


def cible(nom, pos):
    o = bpy.data.objects.new(nom, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = pos
    return o


def viser(cam, cib):
    t = cam.constraints.new("TRACK_TO")
    t.target = cib
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"


def lampe(nom, typ, pos, energie, couleur="#FFFFFF", taille=1.0, vers=None, angle=None):
    l = bpy.data.lights.new(nom, typ)
    l.energy = energie
    l.color = hexa(couleur)
    if typ == "AREA":
        l.size = taille
    if typ in ("POINT", "SPOT"):
        l.shadow_soft_size = taille
    if typ == "SPOT" and angle:
        l.spot_size = angle
        l.spot_blend = 0.6
    o = bpy.data.objects.new(nom, l)
    bpy.context.scene.collection.objects.link(o)
    o.location = pos
    if vers is not None:
        d = Vector(vers) - Vector(pos)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


def cle(o, attr, images_valeurs, interp="BEZIER"):
    """images_valeurs : [(image, valeur), ...]"""
    for f, v in images_valeurs:
        setattr(o, attr, v)
        o.keyframe_insert(attr, frame=f)
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == attr:
                for k in fc.keyframe_points:
                    k.interpolation = interp
                    k.easing = "AUTO"


def lisse(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def oriente_normale(n, rot):
    """Matrice d'orientation : axe Z local le long de la normale, rotation `rot` autour."""
    q = Vector(n).to_track_quat("Z", "Y")
    return q.to_matrix().to_4x4() @ Matrix.Rotation(rot, 4, "Z")
