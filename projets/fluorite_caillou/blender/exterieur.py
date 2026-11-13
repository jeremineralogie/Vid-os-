"""Plans extérieurs : le bloc de roche brute.

A (00:00 -> 00:07,5) : apparition dans le noir, lumière rasante, travelling avant, plongée vers une cassure.
C (00:57,3 -> 01:05) : recul depuis la surface jusqu'au bloc entier, lumière rasante violette et blanche.
Une petite géode de fluorite affleure dans une cassure, invisible dans l'ombre au début, révélée à la fin.

blender -b -P exterieur.py -- apercu 1,4,6.5,58,62,64.9 [echelle]
blender -b -P exterieur.py -- rendu 1 226        (plan A, images ext_####.png)
blender -b -P exterieur.py -- rendu 1720 1950    (plan C)
"""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fl  # noqa: E402

ICI = Path(__file__).resolve().parents[1]
RENDU = ICI / "sources/rendu"
APERCUS = ICI / "sources/apercus"


def pchip_lin(points):
    """Interpolation douce (smoothstep par segment) de [(t, valeur)]."""
    def f(t):
        if t <= points[0][0]:
            return points[0][1]
        for (t0, v0), (t1, v1) in zip(points, points[1:]):
            if t <= t1:
                u = fl.lisse((t - t0) / (t1 - t0))
                return v0 + (v1 - v0) * u
        return points[-1][1]
    return f


def construire():
    fl.vider()
    s = fl.scene_base(1950, echantillons=32, ssr=False)
    s.eevee.bloom_intensity = 0.02
    roche = fl.mat_roche("caillou", clair="#6A646C", sombre="#1A181D", echelle=1.6, relief=1.0)
    c = fl.roche_brute("caillou", rayon=1.0, graine=4, subdiv=6, mat=roche)
    c.rotation_euler = (0.25, 0.15, 0.4)

    # petite géode qui affleure dans une cassure (face tournée vers la droite et l'avant)
    bpy.context.view_layer.update()
    me = c.data
    mw = c.matrix_world
    direction = Vector((0.55, -0.75, 0.25)).normalized()
    meilleur = max(me.vertices, key=lambda v: (mw @ v.co).normalized().dot(direction))
    p_geode = mw @ meilleur.co
    n_geode = (mw.to_3x3() @ meilleur.normal).normalized()
    m_fl = fl.mat_fluorite("fl_ext", "#7650C9", rugosite=0.03)
    m_co = fl.mat_coeur("co_ext", "#35196F")
    rng = random.Random(2)
    for i in range(9):
        off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        off -= n_geode * off.dot(n_geode)
        taille = rng.uniform(0.035, 0.075)
        pos = p_geode + off.normalized() * rng.uniform(0, 0.09) - n_geode * 0.035
        for nom, mat, k in ((f"g{i}", m_fl, 1.0), (f"g{i}c", m_co, 0.55)):
            o = fl.cube_cristal(nom, taille * k, mat, chanfrein=0.004)
            o.location = pos
            o.matrix_world = fl.oriente_normale(n_geode, rng.uniform(0, 6.28))
            o.location = pos
            o.scale = (taille * k,) * 3
    # caméra
    cam = fl.camera("cam", focale=50, ouverture=4.0)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    cib = fl.cible("visee", (0, 0, 0))
    cam.data.dof.focus_object = cib
    fl.viser(cam, cib)

    # point de plongée : la cassure de la géode (on y entre au plan A, on en ressort au plan C)
    entree = p_geode + n_geode * 0.03
    loin = Vector((0.0, -10.6, 1.25))
    pres = Vector((0.15, -8.2, 1.0))
    approche = entree + n_geode * 0.9 + Vector((0, 0, 0.1))
    pos_a = [(0.0, loin), (5.0, pres), (6.4, approche), (7.5, entree + n_geode * 0.012)]
    vis_a = [(0.0, Vector((0, 0, -0.32))), (5.0, Vector((0.05, 0, -0.3))), (6.4, p_geode), (7.5, p_geode)]
    pos_c = [(57.3, entree + n_geode * 0.012), (58.6, approche), (61.5, Vector((0.25, -10.0, 0.95))),
             (65.0, Vector((0.35, -10.6, 1.0)))]
    vis_c = [(57.3, p_geode), (58.6, p_geode), (61.5, Vector((0.05, 0, -0.12))), (65.0, Vector((0.05, 0, -0.12)))]

    def interp(cles, t):
        for (t0, a), (t1, b) in zip(cles, cles[1:]):
            if t <= t1:
                u = min(max((t - t0) / (t1 - t0), 0), 1)
                return a, b, u
        return cles[-1][1], cles[-1][1], 1.0

    for f in list(range(1, 230)) + list(range(1715, 1951)):
        t = (f - 1) / 30
        if t < 30:
            a, b, u = interp(pos_a, t)
            # 0-5 s : travelling lent ; 5-7,5 s : accélération continue vers la cassure
            u = fl.lisse(u) if t < 5 else u ** 2.2 if t < 6.4 else u ** 0.8
            if t < 5:
                u = u * 0.85 + 0.15 * (t / 5)
            pos = a.lerp(b, u)
            av, bv, uv = interp(vis_a, t)
            vis = av.lerp(bv, fl.lisse(uv))
        else:
            a, b, u = interp(pos_c, t)
            u = u ** 0.6 if t < 58.6 else fl.lisse(u) if t < 61.5 else u
            pos = a.lerp(b, u)
            av, bv, uv = interp(vis_c, t)
            vis = av.lerp(bv, fl.lisse(uv))
        pos = pos + Vector((0.004 * math.sin(t * 1.1), 0, 0.003 * math.sin(t * 0.8)))
        cam.location = pos
        cam.keyframe_insert("location", frame=f)
        cib.location = vis
        cib.keyframe_insert("location", frame=f)
    for o in (cam, cib):
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    # rotation très lente du bloc
    fl.cle(c, "rotation_euler", [(1, (0.25, 0.15, 0.4)), (226, (0.25, 0.15, 0.47))], interp="LINEAR")
    fl.cle(c, "rotation_euler", [(1715, (0.25, 0.15, 0.47)), (1950, (0.25, 0.15, 0.37))], interp="LINEAR")
    for o in s.objects:
        if o.name.startswith("g"):
            o.parent = c
            o.matrix_parent_inverse = c.matrix_world.inverted()

    # lumières : rasante (gauche, basse) qui se lève ; à la fin, violet à gauche et blanc à droite
    rasante = fl.lampe("rasante", "AREA", (-3.2, -0.6, 0.25), 0.0, "#E6E6F0", taille=1.2, vers=(0, 0, 0.1))
    fl.cle(rasante.data, "energy", [(1, 0.0), (75, 220.0), (226, 260.0), (1715, 140.0), (1950, 160.0)])
    fl.cle(rasante.data, "color", [(1, fl.hexa("#E6E6F0")), (1715, fl.hexa("#9C7BE6")), (1950, fl.hexa("#9C7BE6"))])
    contre = fl.lampe("contre", "AREA", (2.4, 2.2, 1.6), 0.0, "#B49AEF", taille=1.5, vers=(0, 0, 0))
    fl.cle(contre.data, "energy", [(1, 0.0), (90, 30.0), (226, 40.0), (1715, 40.0), (1950, 60.0)])
    blanc = fl.lampe("blanc_droite", "AREA", (3.0, -1.4, 0.6), 0.0, "#E6E6F0", taille=1.0, vers=(0, 0, 0.1))
    fl.cle(blanc.data, "energy", [(1, 0.0), (226, 0.0), (1715, 150.0), (1950, 170.0)])
    # éclairage d'approche : on suit la caméra quand elle entre dans la cassure (pas de noir brutal)
    proche = fl.lampe("proche", "POINT", tuple(entree + n_geode * 0.4), 0.0, "#E6E6F0", taille=0.2)
    fl.cle(proche.data, "energy", [(150, 0.0), (205, 1.2), (226, 0.4), (1715, 0.4), (1765, 1.2), (1800, 0.0)])
    return s


def principal():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["apercu", "1,4,6.5,58,62,64.9"]
    s = construire()
    if args[0] == "apercu":
        APERCUS.mkdir(parents=True, exist_ok=True)
        s.render.resolution_percentage = int(args[2]) if len(args) > 2 else 50
        s.eevee.taa_render_samples = 8
        for t in (float(x) for x in args[1].split(",")):
            s.frame_set(int(round(t * 30)) + 1)
            s.render.filepath = str(APERCUS / f"ext_{t:05.1f}.png")
            bpy.ops.render.render(write_still=True)
    else:
        RENDU.mkdir(parents=True, exist_ok=True)
        s.render.resolution_percentage = 75
        s.eevee.taa_render_samples = 12
        s.frame_start, s.frame_end = int(args[1]), int(args[2])
        s.render.filepath = str(RENDU / "ext_####")
        s.render.use_overwrite = False
        s.render.use_placeholder = True
        bpy.ops.render.render(animation=True)


principal()
