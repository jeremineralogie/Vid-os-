"""Plan intérieur continu (00:06,8 -> 00:58,4) : fracture, fluides, cavité, croissance des cristaux, macro.

blender -b -P interieur.py -- apercu 8,15,30 [echelle]   -> images fixes (sources/apercus/)
blender -b -P interieur.py -- rendu 205 1755              -> images de l'animation (sources/rendu/int_####.png)

Un seul maillage tubulaire : la fracture (fente étroite et sinueuse) s'ouvre sur une cavité (géode). Le temps
est global (t = (image - 1) / 30), commun au montage.
"""
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fl  # noqa: E402

ICI = Path(__file__).resolve().parents[1]
RENDU = ICI / "sources/rendu"
APERCUS = ICI / "sources/apercus"
DIAG = "diag" in sys.argv

Y0, Y1 = -2.0, 35.0
CAV_A, CAV_B = 21.0, 31.5  # étendue de la cavité le long de y


def profil(y):
    """0 dans la fracture, 1 au cœur de la cavité."""
    if y <= CAV_A or y >= CAV_B:
        return 0.0
    u = (y - CAV_A) / (CAV_B - CAV_A)
    return math.sin(math.pi * u) ** 0.55


def centre(y):
    p = profil(y)
    x = 0.55 * noise.noise(Vector((y * 0.13, 1.3, 0.0))) + 0.25 * noise.noise(Vector((y * 0.31, 7.1, 0.0)))
    z = 0.35 * noise.noise(Vector((y * 0.11, 4.2, 2.0)))
    return Vector((x * (1 - p), y, z * (1 - p) + 0.9 * p))


def demi_axes(y):
    p = profil(y)
    a = 0.27 + 0.09 * noise.noise(Vector((y * 0.4, 2.0, 5.0)))      # demi-largeur de la fente
    b = 1.5 + 0.5 * noise.noise(Vector((y * 0.2, 9.0, 1.0)))       # demi-hauteur
    return a + (3.3 - a) * p, b + (2.7 - b) * p


def tunnel(mat, n_tour=128, pas=0.05):
    bm = bmesh.new()
    anneaux = []
    y = Y0
    while y <= Y1:
        c = centre(y)
        a, b = demi_axes(y)
        p = profil(y)
        anneau = []
        for j in range(n_tour):
            th = 2 * math.pi * j / n_tour
            cs, sn = math.cos(th), math.sin(th)
            ex = 0.55 + 0.45 * p  # fente anguleuse -> cavité arrondie
            x = a * math.copysign(abs(cs) ** ex, cs)
            z = b * math.copysign(abs(sn) ** ex, sn)
            if p > 0 and z < 0:  # plancher de la cavité plus plat
                z *= 1 - 0.35 * p
            q = c + Vector((x, 0, z))
            r = Vector((x, 0, z)).normalized() if (x or z) else Vector((1, 0, 0))
            amp = 0.07 + 0.38 * p
            d = amp * noise.fractal(q * (2.4 - 1.5 * p), 0.55, 2.0, 5 - int(2 * p)) + 0.018 * noise.noise(q * 14)
            anneau.append(bm.verts.new(q + r * d * (1.0 if p else 0.8)))
        anneaux.append(anneau)
        y += pas
    for i in range(len(anneaux) - 1):
        A, B = anneaux[i], anneaux[i + 1]
        for j in range(n_tour):
            k = (j + 1) % n_tour
            bm.faces.new((A[j], B[j], B[k], A[k]))
    bm.normal_update()
    # normales vers l'intérieur du vide
    bm.faces.ensure_lookup_table()
    f = bm.faces[len(bm.faces) // 3]
    if f.normal.dot(centre(f.calc_center_median().y) - f.calc_center_median()) < 0:
        for f in bm.faces:
            f.normal_flip()
    me = bpy.data.meshes.new("tunnel")
    bm.to_mesh(me)
    bm.free()
    o = fl.objet("tunnel", me, mat)
    fl.lisser(o)
    return o


def troncons(o, longueur=2.0):
    """Découpe le tunnel en tronçons le long de y : Eevee n'affiche et n'ombre que ce qui est dans le champ."""
    import bmesh as bmm
    pieces = []
    y = Y0
    while y < Y1:
        bm = bmm.new()
        bm.from_mesh(o.data)
        a, b = y - 0.06, y + longueur + 0.06
        bmm.ops.delete(bm, geom=[f for f in bm.faces if not (a <= f.calc_center_median().y <= b)], context="FACES")
        me = bpy.data.meshes.new(f"tunnel_{len(pieces):02d}")
        bm.to_mesh(me)
        bm.free()
        p = fl.objet(me.name, me, o.data.materials[0])
        pieces.append(p)
        y += longueur
    return pieces


def bvh_de(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    arbre = BVHTree.FromBMesh(bm)
    bm.free()
    return arbre


# ------------------------------------------------------------------ cristaux

def courbe_croissance(t0, t1, fin):
    """Taille relative en fonction du temps : départ lent, croissance, ralentissement (sigmoïde douce)."""
    def s(t):
        u = (t - t0) / (t1 - t0)
        if u <= 0:
            return 0.0
        if u >= 1:
            return fin
        return fin * (u * u * (3 - 2 * u)) ** 0.85
    return s


def poser_cristal(nom, pos, normale, taille, t0, t1, mats, coeur_rel=0.55, enfonce=0.3, inclinaison=0.5, graine=0):
    rng = random.Random(graine)
    m_ext, m_coeur = mats
    ext = fl.cube_cristal(nom, 1.0, m_ext, chanfrein=0.012)
    coeur = fl.cube_cristal(nom + "_c", 1.0, m_coeur, chanfrein=0.02)
    # orientation : un coin ou une face tourné vers la cavité, aléatoirement
    n = Vector(normale).normalized()
    base = fl.oriente_normale(n, rng.uniform(0, math.tau))
    tilt = Matrix.Rotation(rng.uniform(-inclinaison, inclinaison), 4, "X") @ Matrix.Rotation(
        rng.uniform(-inclinaison, inclinaison), 4, "Y")
    rot = (base @ tilt).to_euler()
    for o in (ext, coeur):
        o.rotation_euler = rot
    s = courbe_croissance(t0, t1, taille)
    images = sorted(set([max(1, int(t0 * 30) - 1)] + list(range(int(t0 * 30), int(t1 * 30) + 6, 4))))
    for f in images:
        t = (f - 1) / 30
        v = s(t)
        # le cristal grandit depuis la paroi : son centre avance le long de la normale
        for o, k in ((ext, v), (coeur, min(v, taille * coeur_rel) * 0.97)):
            o.scale = (max(k, 1e-4),) * 3
            o.location = Vector(pos) + n * (v * (0.5 - enfonce))
            o.keyframe_insert("scale", frame=f)
            o.keyframe_insert("location", frame=f)
    for o in (ext, coeur):
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    return ext, coeur


# ------------------------------------------------------------------ caméra

def pchip(points):
    """Interpolation monotone (Fritsch-Carlson) de [(t, v)] -> fonction."""
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    n = len(ts)
    d = [(vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, n - 1)] + [d[-1]]

    def f(t):
        if t <= ts[0]:
            return vs[0]
        if t >= ts[-1]:
            return vs[-1]
        i = max(k for k in range(n - 1) if ts[k] <= t)
        h = ts[i + 1] - ts[i]
        u = (t - ts[i]) / h
        h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
        return h00 * vs[i] + h10 * h * m[i] + h01 * vs[i + 1] + h11 * h * m[i + 1]
    return f


def melange(a, b, k):
    return a + (b - a) * k


def construire():
    fl.vider()
    s = fl.scene_base(1950, volumes=True, echantillons=24, ssr=False)
    s.eevee.volumetric_end = 14
    roche = fl.mat_roche("paroi", clair="#4E4A4F", sombre="#0F0E11", echelle=2.2, relief=0.8)
    pr = roche.node_tree.nodes["Principled BSDF"]
    fl.entree(pr, "Specular").default_value = 0.5  # parois humides
    t = tunnel(roche)
    arbre = bvh_de(t)
    troncons(t)
    bpy.data.objects.remove(t)

    # --------------------------------------------------------- cristaux de la cavité
    rng = random.Random(11)
    mats_petits = (fl.mat_fluorite("fl_p", "#6E48C6", lueur=0.09, opacite=0.55), fl.mat_coeur("co_p", "#41227F"))
    mats_moy = (fl.mat_fluorite("fl_m", "#6A44C0", lueur=0.07, opacite=0.45), fl.mat_coeur("co_m", "#35196F"))
    mats_pale = (fl.mat_fluorite("fl_pale", "#B49AEF", rugosite=0.03, lueur=0.08, opacite=0.3), fl.mat_coeur("co_pale", "#5B3BA8"))
    mats_heros = (fl.mat_fluorite("fl_h", "#6A44C0", rugosite=0.01, lueur=0.05, opacite=0.36), fl.mat_coeur("co_h", "#3B1A80"))

    def sur_paroi(depuis, direction):
        hit = arbre.ray_cast(Vector(depuis), Vector(direction).normalized(), 20)
        if hit[0] is None:
            return None
        pos, nor = hit[0], hit[1]
        if nor.dot(Vector(direction)) > 0:  # normale tournée vers le vide
            nor = -nor
        return pos, nor

    HEROS_POS = None
    r = sur_paroi((0.35, 27.0, 0.9), (0, 0, -1))
    if r:
        HEROS_POS, n_h = r
        poser_cristal("heros", HEROS_POS, Vector((0.05, -0.08, 1)), 0.62, 25.0, 47.0, mats_heros,
                      coeur_rel=0.5, enfonce=0.22, inclinaison=0.12, graine=5)
        # cristal accolé (croissance en groupe)
        poser_cristal("heros2", HEROS_POS + Vector((0.42, 0.28, -0.05)), Vector((0.4, 0.1, 1)), 0.34, 26.5, 46.0,
                      mats_heros, coeur_rel=0.5, enfonce=0.3, inclinaison=0.3, graine=6)

    placees = []
    def libre(p, rayon):
        return all((p - q).length > rayon + rq for q, rq in placees) and (
            HEROS_POS is None or (p - HEROS_POS).length > 0.55 + rayon)

    # 1re génération : nombreux petits cubes (nucléation), 2e : moins nombreux, plus gros
    generations = [(170, (0.04, 0.11), (24.0, 30.0), 7.0, mats_petits),
                   (55, (0.14, 0.36), (27.0, 37.0), 11.0, mats_moy),
                   (25, (0.12, 0.28), (29.0, 38.0), 10.0, mats_pale)]
    k = 0
    for nb, (tmin, tmax), (d0, d1), duree, mats in generations:
        essais = 0
        posees = 0
        while posees < nb and essais < nb * 40:
            essais += 1
            y = rng.uniform(CAV_A + 1.6, CAV_B - 0.8)
            c = centre(y)
            th = rng.uniform(0, math.tau)
            dirn = Vector((math.cos(th), 0, math.sin(th)))
            if dirn.z > 0.75 and rng.random() < 0.7:  # moins au plafond
                continue
            res = sur_paroi(c, dirn)
            if not res:
                continue
            pos, nor = res
            if profil(pos.y) < 0.55:
                continue
            taille = math.exp(rng.uniform(math.log(tmin), math.log(tmax)))
            if not libre(pos, taille * 0.75):
                continue
            # dégager l'axe de la caméra à l'entrée de la cavité
            if pos.y < 23.2 and abs(pos.x - c.x) < 1.0 and pos.z > c.z - 0.3:
                continue
            t0 = rng.uniform(d0, d1)
            poser_cristal(f"cr{k:03d}", pos, nor, taille, t0, t0 + duree * rng.uniform(0.8, 1.3), mats,
                          coeur_rel=rng.uniform(0.45, 0.7), enfonce=rng.uniform(0.25, 0.42), graine=k)
            placees.append((pos, taille * 0.75))
            posees += 1
            k += 1

    # --------------------------------------------------------- cristal de démonstration (ions)
    DEMO_POS = None
    demo = sur_paroi((-0.2, 22.9, 0.9), (-0.55, 0.35, -0.75))
    if demo:
        DEMO_POS, n_d = demo
        poser_cristal("demo", DEMO_POS, n_d, 0.26, 24.3, 34.0, mats_moy, coeur_rel=0.55, enfonce=0.3,
                      inclinaison=0.2, graine=99)
        ions(DEMO_POS + n_d * 0.13, n_d)
        # lumière de modelé du cristal de démonstration (faces et reflets lisibles)
        fl.lampe("demo_cle", "AREA", tuple(DEMO_POS + Vector((0.7, -0.5, 0.9))), 25.0, "#E6E6F0", taille=0.6,
                 vers=tuple(DEMO_POS))
        fl.lampe("demo_contre", "POINT", tuple(DEMO_POS + Vector((-0.3, 0.6, 0.35))), 6.0, "#B49AEF", taille=0.2)

    # --------------------------------------------------------- fluide et particules
    fluide, map_fluide = fl.mat_fluide("fluide", densite=0.07, force=0.7)
    vol = fl.objet("fluide_vol", bpy.data.meshes.new("vol"), fluide)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(vol.data)
    bm.free()
    vol.location = (0, 9.5, 0)
    vol.scale = (2.4, 23.0, 4.4)
    # le fluide s'écoule vers +y (même sens que la caméra) puis se dilue dans la cavité
    for f, yy in ((1, 0.0), (1950, -16.0)):
        map_fluide.inputs["Location"].default_value = (0.0, yy, 0.0)
        map_fluide.inputs["Location"].keyframe_insert("default_value", frame=f)
    for fc in fluide.node_tree.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    brume_cav = fl.objet("brume_cav", bpy.data.meshes.new("brume"), None)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(brume_cav.data)
    bm.free()
    mb = bpy.data.materials.new("brume")
    mb.use_nodes = True
    nt = mb.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vb = nt.nodes.new("ShaderNodeVolumePrincipled")
    vb.inputs["Density"].default_value = 0.018
    vb.inputs["Anisotropy"].default_value = 0.5
    vb.inputs["Color"].default_value = fl.lin("#CFCBDD")
    nt.links.new(vb.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    brume_cav.data.materials.append(mb)
    brume_cav.location = (0, 26.3, 0.9)
    brume_cav.scale = (7.0, 10.5, 6.0)
    brume_cav.hide_render = True

    particules()

    # --------------------------------------------------------- lumières
    cam = fl.camera("cam", focale=22, ouverture=2.8, mise_au_point=1.0)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24
    frontale = fl.lampe("frontale", "POINT", (0, 0, 0), 22.0, "#E6E6F0", taille=0.25)
    frontale.parent = cam
    frontale.location = (0.12, 0.18, 0.05)
    # lueurs chaudes en profondeur de la fracture (fluide chaud), qui avancent avec le fluide
    for i, y in enumerate((8.0, 14.0, 19.5)):
        lp = fl.lampe(f"chaud{i}", "POINT", tuple(centre(y)), 18.0, "#D6A875", taille=0.4)
        fl.cle(lp, "location", [(1, tuple(centre(y))), (1950, tuple(centre(y + 4)))], interp="LINEAR")
    # éclairage de la cavité : clé blanche rasante, contre-jour violet, débouché
    cav = centre(26.0)
    cle_l = fl.lampe("cle_cav", "SPOT", (-2.6, 24.0, 3.0), 650.0, "#E6E6F0", taille=0.35,
                     vers=(0.6, 27.5, -1.0), angle=math.radians(55))
    fl.lampe("violet_cav", "AREA", (2.2, 30.0, 2.8), 70.0, "#7650C9", taille=2.0, vers=(0, 26.5, -0.6))
    fl.lampe("rim_cav", "POINT", (1.8, 28.8, -0.6), 15.0, "#B49AEF", taille=0.5)
    fl.lampe("debouche", "POINT", (0.3, 23.5, 1.2), 25.0, "#E6E6F0", taille=1.0)
    # cristal héros : lumière de modelé (macro), qui révèle transparence et zonation
    if HEROS_POS:
        fl.lampe("heros_cle", "AREA", tuple(HEROS_POS + Vector((-1.2, -0.6, 1.4))), 60.0, "#E6E6F0", taille=0.8,
                 vers=tuple(HEROS_POS))
        fl.lampe("heros_mur", "AREA", tuple(HEROS_POS + Vector((-0.3, -0.4, 1.8))), 120.0, "#E6E6F0", taille=1.2,
                 vers=tuple(HEROS_POS + Vector((0.2, 1.8, 0.2))))
        fl.lampe("heros_arriere", "SPOT", tuple(HEROS_POS + Vector((0.6, 1.6, 0.6))), 420.0, "#B49AEF",
                 taille=0.2, vers=tuple(HEROS_POS), angle=math.radians(35))

    # contre-jours : éclairent les cristaux par l'arrière (la caméra regarde vers +y)
    fl.lampe("contre_cav", "AREA", (0.2, 30.6, 0.2), 260.0, "#DCD8EC", taille=2.0, vers=(0, 25.0, -0.6))
    fl.lampe("contre_bas", "AREA", (-1.5, 29.5, -1.2), 60.0, "#B49AEF", taille=1.0, vers=(0, 24.5, -0.4))
    for o in bpy.context.scene.objects:
        if o.type == "LIGHT":
            o.data.use_shadow = o.name in ("frontale", "cle_cav", "heros_cle")
            if o.data.use_shadow:
                o.data.shadow_buffer_clip_start = 0.02
    bpy.context.scene.eevee.shadow_cube_size = "512"
    animer_camera(cam, HEROS_POS, arbre, DEMO_POS)
    return s, cam


def ions(cible, normale):
    """Illustration : ions Ca2+ (clairs) et F- (violets) qui rejoignent le cristal (rapport 1:2)."""
    rng = random.Random(4)
    m_ca = fl.mat_emission("ion_ca", "#E6E6F0", 1.3)
    m_f = fl.mat_emission("ion_f", "#B49AEF", 1.6)
    me_ca = bpy.data.meshes.new("ca")
    me_f = bpy.data.meshes.new("f")
    for me, r in ((me_ca, 0.011), (me_f, 0.0075)):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        bm.to_mesh(me)
        bm.free()
    for i in range(54):
        est_ca = i % 3 == 0
        o = fl.objet(f"ion{i:02d}", me_ca if est_ca else me_f, m_ca if est_ca else m_f)
        fl.lisser(o)
        t_arr = rng.uniform(26.0, 33.0)
        depart = cible + Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.5), rng.uniform(-0.2, 0.8))) + normale * 0.4
        arrivee = cible + Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(-0.04, 0.04)))
        t_dep = t_arr - rng.uniform(2.5, 4.0)
        f_apparait, f_dep, f_arr = int(23.6 * 30), int(t_dep * 30), int(t_arr * 30)
        o.location = depart
        o.scale = (0.0,) * 3
        o.keyframe_insert("scale", frame=f_apparait - 10)
        o.scale = (1.0,) * 3
        o.keyframe_insert("scale", frame=f_apparait + 12)
        o.keyframe_insert("location", frame=f_dep)
        # dérive brownienne puis attraction vers la face
        milieu = depart.lerp(arrivee, 0.5) + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.1))
        o.location = milieu
        o.keyframe_insert("location", frame=(f_dep + f_arr) // 2)
        o.location = arrivee
        o.keyframe_insert("location", frame=f_arr)
        o.keyframe_insert("scale", frame=f_arr - 4)
        o.scale = (0.0,) * 3
        o.keyframe_insert("scale", frame=f_arr + 3)
        o.keyframe_insert("scale", frame=f_arr + 4)


def particules():
    """Particules en suspension dans le fluide (illustration), entraînées vers +y."""
    rng = random.Random(8)
    mats = [fl.mat_emission("part_chaud", "#D6A875", 3.0), fl.mat_emission("part_blanc", "#E6E6F0", 2.0)]
    me = bpy.data.meshes.new("part")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    for i in range(260):
        y0 = rng.uniform(1.5, 27.0)
        c = centre(y0)
        a, b = demi_axes(y0)
        p = c + Vector((rng.uniform(-0.75, 0.75) * a, 0, rng.uniform(-0.8, 0.8) * b))
        o = fl.objet(f"p{i:03d}", me, mats[i % 2])
        r = rng.uniform(0.0025, 0.009)
        o.scale = (r,) * 3
        v = rng.uniform(0.18, 0.45)
        o.location = p
        o.keyframe_insert("location", frame=1)
        q = centre(y0 + v * 65)
        o.location = p + Vector((q.x - c.x, v * 65, q.z - c.z))
        o.keyframe_insert("location", frame=1950)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            if fc.array_index != 1:
                mo = fc.modifiers.new("NOISE")
                mo.scale = rng.uniform(40, 90)
                mo.strength = 0.05
                mo.phase = rng.uniform(0, 100)


# ------------------------------------------------------------------ trajectoire

def animer_camera(cam, heros, arbre, demo=None):
    """Position et visée, calculées pour chaque image (temps global)."""
    hz = heros if heros is not None else Vector((0.35, 27.0, -0.9))
    dz = demo if demo is not None else Vector((-0.6, 23.4, 0.0))
    # avancée dans la fracture (y en fonction du temps)
    y_t = fl_pchip = pchip([(6.8, -1.6), (8.5, 1.6), (12.0, 5.0), (17.0, 10.6), (22.0, 17.0), (26.0, 20.6),
                            (35.0, 21.9)])

    def corridor(t):
        y = y_t(t)
        c = centre(y)
        return c + Vector((0, 0, 0.12)), centre(y + 1.6) + Vector((0, 0, 0.05))

    # cavité : suite de positions clés (t, position, visée, focale, mise au point)
    cles = [
        (26.0, None, None, 22, None),
        (30.0, dz + Vector((0.45, -0.8, 0.85)), dz + Vector((0, 0.05, 0.08)), 32, None),
        (34.0, dz + Vector((0.2, -0.62, 0.62)), dz + Vector((0, 0.05, 0.1)), 38, None),
        (37.0, Vector((-0.6, 22.4, 0.9)), Vector((-0.1, 24.8, 0.0)), 28, None),
        (41.0, Vector((-1.7, 24.2, 0.6)), Vector((0.2, 26.6, -0.3)), 30, None),
        (45.5, Vector((1.2, 24.8, 0.6)), hz + Vector((0, 0, 0.25)), 35, None),
        (48.0, hz + Vector((1.5, -1.5, 1.35)), hz + Vector((0, 0, 0.2)), 40, None),
        (51.0, hz + Vector((0.85, -1.6, 1.1)), hz + Vector((0.0, 0, 0.2)), 45, None),
        (54.0, hz + Vector((-0.85, -1.45, 1.15)), hz + Vector((0.0, 0.05, 0.22)), 50, None),
        (56.5, hz + Vector((-1.5, -0.5, 1.15)), hz + Vector((0.0, 0.05, 0.2)), 50, None),
        (58.4, Vector((-0.1, 21.2, 1.0)), Vector((0.2, 26.0, 0.3)), 24, None),
    ]
    p0, v0 = corridor(26.0)
    cles[0] = (26.0, p0, v0, 22, None)
    ts = [c[0] for c in cles]
    comp = lambda i, j: pchip([(c[0], c[i][j]) for c in cles])  # noqa: E731
    pos_f = [comp(1, j) for j in range(3)]
    vis_f = [comp(2, j) for j in range(3)]
    foc_f = pchip([(c[0], c[3]) for c in cles])

    cib = fl.cible("visee", (0, 0, 0))
    cam.data.dof.focus_object = cib
    fl.viser(cam, cib)
    for f in range(205, 1757):
        t = (f - 1) / 30
        if t <= 26.0:
            p, v = corridor(t)
            foc = 22
        else:
            p = Vector([g(t) for g in pos_f])
            v = Vector([g(t) for g in vis_f])
            foc = foc_f(t)
            # garde au sol : jamais dans la paroi (plancher bosselé de la cavité)
            # rayon lancé depuis la caméra (un départ plus haut toucherait le dessus d'un plafond bas)
            sol = arbre.ray_cast(p + Vector((0, 0, 0.05)), Vector((0, 0, -1)), 6)[0]
            if sol is not None and p.z < sol.z + 0.32:
                p = Vector((p.x, p.y, sol.z + 0.32))
            ancien = arbre.ray_cast(p + Vector((0, 0, 1.2)), Vector((0, 0, -1)), 6)[0]
            if DIAG and ancien is not None and p.z < ancien.z + 0.32 - 1e-4:
                print("DIAG", f)
        # micro-flottement « caméra portée » très doux
        p = p + Vector((0.006 * math.sin(t * 1.3), 0, 0.005 * math.sin(t * 0.9 + 1)))
        cam.location = p
        cam.keyframe_insert("location", frame=f)
        cib.location = v
        cib.keyframe_insert("location", frame=f)
        cam.data.lens = foc
        cam.data.keyframe_insert("lens", frame=f)
        # mise au point : sur la visée en macro, plus loin dans la fracture
        cam.data.dof.aperture_fstop = 5.6 if t < 46 else 4.0
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    for o in (cam, cib, cam.data, cam.data.dof):
        ad = getattr(o, "animation_data", None)
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def principal():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["apercu", "30"]
    s, cam = construire()
    if args[0] == "diag":
        return
    if args[0] == "apercu":
        APERCUS.mkdir(parents=True, exist_ok=True)
        ech = int(args[2]) if len(args) > 2 else 50
        s.render.resolution_percentage = ech
        s.eevee.taa_render_samples = 8
        for t in (float(x) for x in args[1].split(",")):
            s.frame_set(int(round(t * 30)) + 1)
            s.render.filepath = str(APERCUS / f"int_{t:05.1f}.png")
            bpy.ops.render.render(write_still=True)
    elif args[0] == "test":  # chronométrage : 3 images à partir de args[1], échelle args[2], échantillons args[3]
        import time
        s.render.resolution_percentage = int(args[2])
        s.eevee.taa_render_samples = int(args[3])
        s.frame_start, s.frame_end = int(args[1]), int(args[1]) + 2
        s.render.filepath = str(APERCUS / "test_####")
        T = [time.time()]
        def h(*a):
            T.append(time.time())
            print("IMAGE", round(T[-1] - T[-2], 1), flush=True)
        bpy.app.handlers.render_post.append(h)
        bpy.ops.render.render(animation=True)
    elif args[0] == "blend":
        bpy.ops.wm.save_as_mainfile(filepath=str(ICI / "sources/interieur.blend"))
    else:
        RENDU.mkdir(parents=True, exist_ok=True)
        s.render.resolution_percentage = 75
        s.eevee.taa_render_samples = 10
        s.frame_start, s.frame_end = int(args[1]), int(args[2])
        s.frame_step = int(args[3]) if len(args) > 3 else 1
        s.render.filepath = str(RENDU / "int_####")
        s.render.use_overwrite = False
        s.render.use_placeholder = True
        bpy.ops.render.render(animation=True)


principal()
