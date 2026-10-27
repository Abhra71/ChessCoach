"""Trailer 2 ("Refined"): every 3D shot, built from scratch in Blender (no downloaded models), dark and dramatic.

Run one shot:  blender -b --factory-startup -P installer/trailer3d/scene.py -- <shot> <outdir> [preview]
  shot: reveal | rank | blunder | cradle | mate      preview: one small frame from the middle, to check the look
The story: ordinary wooden pieces make a mistake; as the moves get right, the pieces are crystal.
Board squares are 1.0 wide; the board's centre is (0, 0); files a-h run along x, ranks 1-8 along y.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = args[0] if args else "reveal"
OUT = os.path.abspath(args[1] if len(args) > 1 else "frames")
PREVIEW = len(args) > 2 and args[2] == "preview"
FPS = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS


def sq(name):
    """The centre of a square like "e4" (z = 0, the board's top)."""
    return Vector(("abcdefgh".index(name[0]) - 3.5, int(name[1]) - 4.5, 0.0))


# ================= materials =================
def material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def wood(name, light, dark, rough=0.38, scale=7.0):
    m, n, l, b = material(name)
    coord, mapping = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 9.0)  # grain runs up the piece, like turned wood
    wave = n.new("ShaderNodeTexWave")
    wave.wave_type, wave.bands_direction = "RINGS", "Z"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 6.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*light, 1)
    ramp.color_ramp.elements[1].color = (*dark, 1)
    l.new(coord.outputs["Object"], mapping.inputs["Vector"])
    l.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    l.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.12
    return m


def crystal(name, tint):
    m, n, l, b = material(name)
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = 0.015
    b.inputs["IOR"].default_value = 1.52
    b.inputs["Transmission Weight"].default_value = 1.0
    m.surface_render_method = "DITHERED"
    return m


def marble():
    m, n, l, b = material("marble")
    coord = n.new("ShaderNodeTexCoord")
    checker = n.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 0.5  # a checker cell is 1 / (2 x scale) = one square
    checker.inputs["Color1"].default_value = (0.012, 0.011, 0.011, 1)
    checker.inputs["Color2"].default_value = (0.42, 0.40, 0.37, 1)
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 12.0
    wave = n.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 1.1
    wave.inputs["Distortion"].default_value = 10.0
    wave.inputs["Detail"].default_value = 9.0
    veins = n.new("ShaderNodeValToRGB")
    veins.color_ramp.elements[0].position, veins.color_ramp.elements[0].color = 0.82, (1, 1, 1, 1)
    veins.color_ramp.elements[1].position, veins.color_ramp.elements[1].color = 0.99, (0.35, 0.33, 0.30, 1)
    mix = n.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.7
    l.new(coord.outputs["Object"], checker.inputs["Vector"])
    l.new(coord.outputs["Object"], noise.inputs["Vector"])
    l.new(noise.outputs["Color"], wave.inputs["Vector"])
    l.new(wave.outputs["Fac"], veins.inputs["Fac"])
    l.new(checker.outputs["Color"], mix.inputs[6])
    l.new(veins.outputs["Color"], mix.inputs[7])
    l.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.10
    b.inputs["Coat Weight"].default_value = 0.8
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


MAT = {
    "wood_w": wood("boxwood", (0.62, 0.45, 0.26), (0.48, 0.32, 0.17)),
    "wood_b": wood("ebony", (0.055, 0.035, 0.025), (0.02, 0.012, 0.01), rough=0.3),
    "crystal_w": crystal("crystal", (0.99, 0.985, 0.97)),
    "crystal_b": crystal("smoke", (0.30, 0.27, 0.25)),
}


# ================= pieces: turned shapes (radius, height), like on a lathe =================
FOOT = [(0.000, 0.000), (0.330, 0.000), (0.343, 0.013), (0.346, 0.033), (0.335, 0.053), (0.310, 0.064),
        (0.303, 0.079), (0.288, 0.088), (0.275, 0.103), (0.262, 0.118)]
PROFILES = {
    "pawn": FOOT + [(0.215, 0.140), (0.178, 0.175), (0.146, 0.235), (0.121, 0.320), (0.106, 0.410), (0.100, 0.470),
                    (0.163, 0.490), (0.187, 0.503), (0.191, 0.516), (0.183, 0.529), (0.130, 0.544), (0.108, 0.557),
                    (0.113, 0.574), (0.146, 0.606), (0.182, 0.655), (0.200, 0.712), (0.198, 0.770), (0.182, 0.827),
                    (0.152, 0.877), (0.108, 0.914), (0.060, 0.935), (0.000, 0.943)],
    "rook": FOOT + [(0.232, 0.140), (0.205, 0.180), (0.190, 0.260), (0.180, 0.420), (0.176, 0.600), (0.182, 0.700),
                    (0.230, 0.730), (0.246, 0.745), (0.246, 0.765), (0.226, 0.780), (0.228, 0.800), (0.262, 0.830),
                    (0.268, 1.040), (0.190, 1.040), (0.190, 0.985), (0.000, 0.985)],
    "bishop": FOOT + [(0.212, 0.140), (0.172, 0.180), (0.138, 0.260), (0.112, 0.380), (0.096, 0.520),
                      (0.090, 0.600), (0.170, 0.625), (0.192, 0.640), (0.192, 0.660), (0.150, 0.678), (0.104, 0.690),
                      (0.100, 0.710), (0.142, 0.760), (0.175, 0.840), (0.180, 0.930), (0.162, 1.030),
                      (0.120, 1.120), (0.065, 1.190), (0.040, 1.215), (0.055, 1.235), (0.060, 1.262),
                      (0.048, 1.290), (0.022, 1.305), (0.000, 1.308)],
    "queen": FOOT + [(0.222, 0.140), (0.185, 0.185), (0.152, 0.280), (0.124, 0.430), (0.108, 0.600),
                     (0.104, 0.760), (0.110, 0.880), (0.195, 0.905), (0.212, 0.925), (0.205, 0.945),
                     (0.130, 0.965), (0.122, 0.990), (0.160, 1.120), (0.212, 1.300), (0.238, 1.380),
                     (0.200, 1.395), (0.120, 1.420), (0.075, 1.450), (0.068, 1.480), (0.055, 1.515),
                     (0.030, 1.540), (0.000, 1.546)],
    "king": FOOT + [(0.226, 0.140), (0.190, 0.190), (0.158, 0.290), (0.130, 0.450), (0.114, 0.630),
                    (0.110, 0.800), (0.116, 0.930), (0.205, 0.955), (0.224, 0.975), (0.216, 0.995),
                    (0.136, 1.015), (0.128, 1.040), (0.165, 1.170), (0.205, 1.330), (0.212, 1.400),
                    (0.170, 1.430), (0.100, 1.470), (0.000, 1.480)],
    "knight": FOOT + [(0.228, 0.140), (0.215, 0.180), (0.205, 0.230), (0.000, 0.230)],
}
HEIGHT = {"pawn": 0.943, "rook": 1.04, "bishop": 1.308, "queen": 1.546, "king": 1.75, "knight": 1.20}


def turned(name, profile, segments=96):
    verts, faces, n = [], [], len(profile)
    for s in range(segments):
        a = 2 * math.pi * s / segments
        verts += [(r * math.cos(a), r * math.sin(a), z) for r, z in profile]
    for s in range(segments):
        t = (s + 1) % segments
        for i in range(n - 1):
            faces.append((s * n + i, t * n + i, t * n + i + 1, s * n + i + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    weld = obj.modifiers.new("weld", "WELD")
    weld.merge_threshold = 1e-4
    return obj


def apply_all(obj):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def cut(obj, cutter):
    mod = obj.modifiers.new("cut", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    apply_all(obj)
    bpy.data.objects.remove(cutter)


def box(name, size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    b = bpy.context.active_object
    b.name, b.scale = name, size
    return b


def knight_head(name):
    """The horse's head: its side view, extruded and bevelled (facing +x)."""
    side = [(-0.22, 0.22), (0.18, 0.22), (0.20, 0.30), (0.18, 0.40), (0.14, 0.50), (0.17, 0.56), (0.25, 0.61),
            (0.35, 0.66), (0.43, 0.71), (0.465, 0.76), (0.45, 0.81), (0.39, 0.85), (0.31, 0.88), (0.26, 0.93),
            (0.22, 1.00), (0.18, 1.07), (0.15, 1.14), (0.12, 1.22), (0.085, 1.15), (0.05, 1.12), (0.02, 1.19),
            (-0.01, 1.11), (-0.07, 1.06), (-0.14, 0.99), (-0.20, 0.89), (-0.25, 0.76), (-0.28, 0.61),
            (-0.28, 0.46), (-0.26, 0.33)]
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "2D"
    spline = curve.splines.new("POLY")
    spline.points.add(len(side) - 1)
    for p, (x, y) in zip(spline.points, side):
        p.co = (x, y, 0, 1)
    spline.use_cyclic_u = True
    curve.extrude, curve.bevel_depth, curve.bevel_resolution = 0.075, 0.05, 8
    curve.fill_mode = "BOTH"
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.rotation_euler = (math.radians(90), 0, 0)  # stand the side view up: the head faces +x
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(rotation=True)
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = 1
    apply_all(obj)
    return obj


TEMPLATES = {}


def template(kind):
    """One mesh per kind, shared by every piece of that kind."""
    if kind in TEMPLATES:
        return TEMPLATES[kind]
    obj = turned(f"t_{kind}", PROFILES[kind])
    apply_all(obj)
    if kind == "rook":  # four notches in the crown
        for i in range(4):
            a = i * math.pi / 2
            cut(obj, box("notch", (0.62, 0.09, 0.14), (0, 0, 1.02), (0, 0, a)))
    if kind == "bishop":  # the mitre's slit
        cut(obj, box("slit", (0.5, 0.035, 0.32), (0.05, 0, 1.08), (0, math.radians(-38), 0)))
    if kind == "king":  # the cross
        for size, z in (((0.07, 0.07, 0.26), 1.60), ((0.20, 0.07, 0.07), 1.62)):
            c = box("cross", size, (0, 0, z))
            bev = c.modifiers.new("bevel", "BEVEL")
            bev.width, bev.segments = 0.012, 3
            apply_all(c)
            join = obj.modifiers.new("join", "BOOLEAN")
            join.operation, join.object, join.solver = "UNION", c, "EXACT"
            apply_all(obj)
            bpy.data.objects.remove(c)
    if kind == "queen":  # the coronet: eight small balls round the crown
        for i in range(8):
            a = i * math.pi / 4
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.034, location=(0.215 * math.cos(a), 0.215 * math.sin(a), 1.40))
            ball = bpy.context.active_object
            join = obj.modifiers.new("join", "BOOLEAN")
            join.operation, join.object, join.solver = "UNION", ball, "EXACT"
            apply_all(obj)
            bpy.data.objects.remove(ball)
    if kind == "knight":
        head = knight_head("t_knight_head")
        join = obj.modifiers.new("join", "BOOLEAN")
        join.operation, join.object, join.solver = "UNION", head, "EXACT"
        apply_all(obj)
        bpy.data.objects.remove(head)
    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(40))
    obj.hide_render = obj.hide_viewport = True
    TEMPLATES[kind] = obj
    return obj


def piece(kind, square, side, look="wood", turn=0.0):
    """A piece on a square: side "w" or "b", look "wood" or "crystal"."""
    obj = bpy.data.objects.new(f"{kind}_{square}", template(kind).data)
    scene.collection.objects.link(obj)
    obj.data = obj.data.copy()  # its own material
    obj.data.materials.clear()
    obj.data.materials.append(MAT[f"{look}_{side}"])
    obj.location = sq(square)
    obj.rotation_euler = (0, 0, math.radians(turn if side == "w" else 180 + turn))
    return obj


# ================= the board, the room, the light =================
def board():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.06))
    b = bpy.context.active_object
    b.name, b.scale = "board", (8.0, 8.0, 0.12)
    bev = b.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.01, 3
    b.data.materials.append(marble())
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.08))
    frame = bpy.context.active_object
    frame.name, frame.scale = "frame", (8.7, 8.7, 0.13)
    bev = frame.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.04, 4
    frame.data.materials.append(wood("frame", (0.09, 0.05, 0.03), (0.05, 0.025, 0.015), rough=0.25, scale=3.0))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.145))
    floor = bpy.context.active_object
    m, n, l, bsdf = material("floor")
    bsdf.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    floor.data.materials.append(m)
    return b


def lights(warm=1.0, haze=False):
    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    if haze:  # light shafts: a thin haze in the room (EEVEE shots only; Cycles would take far longer)
        vol = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = 0.0035
        vol.inputs["Anisotropy"].default_value = 0.6  # the beam glows when you look towards the light
        world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes["World Output"].inputs["Volume"])

    def lamp(name, kind, loc, aim, power, color, size=0.5, spot=None):
        data = bpy.data.lights.new(name, kind)
        data.energy, data.color = power, color
        if kind == "AREA":
            data.size = size
        if kind == "SPOT":
            data.spot_size, data.spot_blend = math.radians(spot or 28), 0.35
            data.shadow_soft_size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        scene.collection.objects.link(obj)
        direction = Vector(aim) - Vector(loc)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return obj

    key = lamp("key", "SPOT", (-4.5, -5.0, 7.5), (0, 0, 0), 9000 * warm, (1.0, 0.82, 0.62), size=0.35, spot=30)
    rim = lamp("rim", "SPOT", (3.0, 7.0, 3.2), (0, 0, 0.5), 2600, (0.62, 0.74, 1.0), size=0.8, spot=40)
    fill = lamp("fill", "AREA", (6.0, -4.0, 1.6), (0, 0, 0.4), 40, (1.0, 0.9, 0.8), size=4.0)
    return key, rim, fill


def glow(where=(0, 9.0, 2.2), size=12, color=(0.85, 0.52, 0.26), strength=0.8, turn=0):
    """A soft warm glow far behind the pieces: glass shows what's behind it, and in a black room that's nothing."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=where, rotation=(math.radians(90), 0, math.radians(turn)))
    g = bpy.context.active_object
    m, n, l, b = material("glow")
    coord, grad, ramp = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeTexGradient"), n.new("ShaderNodeValToRGB")
    grad.gradient_type = "SPHERICAL"
    mapping = n.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.0 / size, 2.0 / size, 1)
    l.new(coord.outputs["Object"], mapping.inputs["Vector"])
    l.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (0, 0, 0, 1), (*color, 1)
    l.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    l.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    g.data.materials.append(m)
    g.visible_shadow = False
    return g


# ================= camera =================
def camera(lens=50, fstop=2.0):
    data = bpy.data.cameras.new("cam")
    data.lens, data.sensor_width = lens, 36
    data.dof.use_dof, data.dof.aperture_fstop = True, fstop
    cam = bpy.data.objects.new("cam", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    focus = bpy.data.objects.new("focus", None)
    scene.collection.objects.link(focus)
    data.dof.focus_object = focus
    look = cam.constraints.new("TRACK_TO")
    look.target, look.track_axis, look.up_axis = focus, "TRACK_NEGATIVE_Z", "UP_Y"
    return cam, focus


def keys(obj, path, frames_values, interp="BEZIER"):
    """Keyframes: [(frame, value), ...] on obj.<path> (a vector or a number)."""
    for f, v in frames_values:
        setattr(obj, path, v)
        obj.keyframe_insert(path, frame=f)


def slide(obj, a, b, f0, f1, lift=0.0):
    """A piece slid along the board from a to b, easing out like a hand placing it."""
    pa, pb = sq(a), sq(b)
    keys(obj, "location", [(f0, pa), (f1, pb)])
    if lift:
        mid = (pa + pb) / 2 + Vector((0, 0, lift))
        keys(obj, "location", [((f0 + f1) // 2, mid)])


# ================= the positions =================
START = {"w": [("rook", "a1"), ("knight", "b1"), ("bishop", "c1"), ("queen", "d1"), ("king", "e1"),
               ("bishop", "f1"), ("knight", "g1"), ("rook", "h1")] + [("pawn", f"{c}2") for c in "abcdefgh"],
         "b": [("rook", "a8"), ("knight", "b8"), ("bishop", "c8"), ("queen", "d8"), ("king", "e8"),
               ("bishop", "f8"), ("knight", "g8"), ("rook", "h8")] + [("pawn", f"{c}7") for c in "abcdefgh"]}


def setup(position, look):
    return {sqr: piece(kind, sqr, side, look) for side, pieces in position.items() for kind, sqr in pieces}


# ================= the shots =================
def shot_reveal():
    """0-6 s: darkness; a light finds one wooden pawn; the camera creeps in."""
    board()
    key, rim, fill = lights(haze=True)
    p = piece("pawn", "e4", "w", "wood")
    for k in ("d6", "f7", "c5"):
        piece("pawn", k, "b", "wood")
    piece("knight", "g6", "b", "wood", turn=-30)
    cam, focus = camera(lens=85, fstop=1.6)
    focus.location = sq("e4") + Vector((0, 0, 0.55))
    keys(cam, "location", [(1, sq("e4") + Vector((-2.6, -4.2, 0.85))), (6 * FPS, sq("e4") + Vector((-1.6, -2.7, 0.62)))])
    keys(key.data, "energy", [(1, 0.0), (int(2.4 * FPS), 9000.0)])
    keys(rim.data, "energy", [(1, 0.0), (int(3.5 * FPS), 2200.0)])
    return 6 * FPS


def shot_rank():
    """6 s: a low glide along White's back rank, wood, shallow focus pulling from piece to piece."""
    board()
    lights(haze=True)
    setup(START, "wood")
    cam, focus = camera(lens=85, fstop=1.6)
    keys(cam, "location", [(1, Vector((-6.5, -8.4, 1.05))), (6 * FPS, Vector((-1.0, -9.0, 1.15)))])
    keys(focus, "location", [(1, sq("b1") + Vector((0, 0, 0.6))), (6 * FPS, sq("f1") + Vector((0, 0, 0.7)))])
    return 6 * FPS


def shot_blunder():
    """5 s, slow motion: a bishop slides in and knocks a knight over; it tips, rolls and settles (real physics)."""
    b = board()
    lights(haze=True)
    bishop = piece("bishop", "b2", "w", "wood")
    knight = piece("knight", "e5", "b", "wood", turn=20)
    for k, s, side in (("pawn", "f6", "b"), ("pawn", "c3", "w"), ("king", "g7", "b")):
        piece(k, s, side, "wood")
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.substeps_per_frame, rbw.solver_iterations = 40, 30
    rbw.time_scale = 0.35  # slow motion
    rbw.point_cache.frame_start, rbw.point_cache.frame_end = 1, 5 * FPS

    def body(obj, kind, mass=0.05, kinematic=False):
        bpy.context.view_layer.objects.active = obj
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.ops.rigidbody.object_add(type=kind)
        rb = obj.rigid_body
        rb.collision_shape, rb.mass, rb.friction, rb.restitution = "CONVEX_HULL", mass, 0.55, 0.15
        rb.kinematic = kinematic
        rb.collision_margin = 0.002
        return rb

    body(b, "PASSIVE").collision_shape = "BOX"
    body(knight, "ACTIVE")
    body(bishop, "ACTIVE", kinematic=True)
    # the bishop glides diagonally b2 -> e5 and shoves into the knight, then the physics takes over
    target = sq("e5") + (sq("b2") - sq("e5")).normalized() * 0.43
    keys(bishop, "location", [(1, sq("b2")), (int(1.2 * FPS), target + (sq("e5") - target) * 0.0),
                              (int(1.9 * FPS), sq("e5") + (sq("b2") - sq("e5")).normalized() * 0.18)])
    bpy.ops.ptcache.bake_all(bake=True)
    cam, focus = camera(lens=55, fstop=2.0)
    # from the side of the bishop's path: it comes in from the left, the knight falls away to the right
    keys(cam, "location", [(1, sq("e5") + Vector((1.0, -4.2, 0.65))), (5 * FPS, sq("e5") + Vector((1.6, -3.6, 0.5)))])
    keys(focus, "location", [(1, sq("d4") + Vector((0, 0, 0.5))), (int(1.4 * FPS), sq("e5") + Vector((0.2, 0, 0.45))),
                             (5 * FPS, sq("e5") + Vector((0.5, 0.2, 0.25)))])
    return 5 * FPS


def shot_cradle():
    """8 s, crystal: the right move. A rook slides into a row of pawns; the push runs through them and only the
    last one moves on, like Newton's cradle (the middle ones never move)."""
    board()
    lights()
    glow()
    rook = piece("rook", "a4", "w", "crystal")
    row = [piece("pawn", s, "b" if i % 2 else "w", "crystal") for i, s in enumerate(("d4", "e4", "f4", "g4"))]
    gap = 0.70  # the pawns touch: the row is pushed together
    for i, p in enumerate(row):
        p.location = sq("d4") + Vector((i * gap, 0, 0))
    hit = int(2.4 * FPS)
    touch = row[0].location - Vector((0.30 + 0.33, 0, 0))
    keys(rook, "location", [(1, sq("a4")), (hit, touch)])
    last = row[-1]
    start = last.location.copy()
    keys(last, "location", [(hit, start), (hit + int(0.6 * FPS), start + Vector((0.85, 0, 0))),
                            (hit + int(1.6 * FPS), start + Vector((1.25, 0, 0)))])  # friction slows it
    cam, focus = camera(lens=50, fstop=2.8)
    keys(cam, "location", [(1, Vector((-0.6, -4.6, 0.75))), (8 * FPS, Vector((1.6, -4.2, 0.6)))])
    keys(focus, "location", [(1, sq("b4") + Vector((0, 0, 0.5))), (hit, sq("d4") + Vector((0.6, 0, 0.5))),
                             (8 * FPS, start + Vector((1.1, 0, 0.45)))])
    return 8 * FPS


def shot_mate():
    """6 s, crystal: checkmate. The black king tips over slowly, rocks, and lies still; light runs through the glass."""
    board()
    lights(warm=1.15)
    glow(where=(-4.0, -3.0, 2.4), size=12, turn=-60)
    king = piece("king", "g8", "b", "crystal")
    for kind, s, side in (("queen", "g7", "w"), ("king", "g6", "w"), ("rook", "a8", "w"), ("pawn", "h7", "b"),
                          ("pawn", "f7", "b")):
        piece(kind, s, side, "crystal")
    # tipping about the edge of its foot: slow, then gravity takes it; one small bounce, a rock, still
    pivot = sq("g8") + Vector((0.34, 0, 0))
    king.location = pivot
    king.data.transform(__import__("mathutils").Matrix.Translation(Vector((-0.34, 0, 0))))
    f0 = int(1.2 * FPS)
    angles = [(1, 0), (f0, 0), (f0 + 18, 12), (f0 + 34, 45), (f0 + 44, 84), (f0 + 49, 90), (f0 + 54, 86),
              (f0 + 60, 90), (f0 + 66, 89), (f0 + 72, 90)]
    for f, a in angles:
        king.rotation_euler = (0, math.radians(a), math.radians(180))
        king.keyframe_insert("rotation_euler", frame=f)
    cam, focus = camera(lens=60, fstop=2.4)
    # from the north-east, outside the board: the king in front, its attackers behind it, the glow beyond
    keys(cam, "location", [(1, sq("g8") + Vector((3.6, 2.6, 0.95))), (6 * FPS, sq("g8") + Vector((2.8, 2.0, 0.6)))])
    keys(focus, "location", [(1, sq("g8") + Vector((0, 0, 0.8))), (f0 + 49, sq("g8") + Vector((0.6, 0, 0.25)))])
    return 6 * FPS


SHOTS = {"reveal": (shot_reveal, "EEVEE"), "rank": (shot_rank, "EEVEE"), "blunder": (shot_blunder, "EEVEE"),
         "cradle": (shot_cradle, "CYCLES"), "mate": (shot_mate, "CYCLES")}

# ================= render =================
build, engine = SHOTS[SHOT]
length = build()
scene.frame_start, scene.frame_end = 1, length
r = scene.render
r.resolution_x, r.resolution_y = 1920, 1080
r.resolution_percentage = 50 if PREVIEW else 100
r.image_settings.file_format = "PNG"
r.film_transparent = False
r.use_motion_blur = not PREVIEW
r.motion_blur_shutter = 0.4
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - High Contrast"
if engine == "CYCLES":
    r.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == kind
            break
        except TypeError:
            continue
    scene.cycles.device = "GPU"
    scene.cycles.samples = 8 if PREVIEW else 16
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces, scene.cycles.transmission_bounces = 10, 10
    r.use_persistent_data = True
else:
    r.engine = "BLENDER_EEVEE"
    ee = scene.eevee
    for attr, value in (("use_raytracing", True), ("taa_render_samples", 16 if PREVIEW else 48),
                        ("use_volumetric_shadows", True), ("volumetric_tile_size", "4"), ("use_shadows", True)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, value)
            except (TypeError, ValueError):
                pass
os.makedirs(OUT, exist_ok=True)
if PREVIEW:
    for f in [int(x) for x in os.environ.get("KW_FRAMES", "").split(",") if x] or (max(1, length // 3), max(1, 2 * length // 3)):
        scene.frame_set(f)
        r.filepath = os.path.join(OUT, f"{SHOT}_preview_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
else:
    r.filepath = os.path.join(OUT, f"{SHOT}_")
    bpy.ops.render.render(animation=True)
print("DONE", SHOT, length, "frames", engine)
