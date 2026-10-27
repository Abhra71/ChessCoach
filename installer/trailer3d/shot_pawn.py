"""Trailer 2 ("Refined"), test shot 1: one crystal pawn on a dark marble square, studio light, shallow focus.

Run:  blender --background --factory-startup --python installer/trailer3d/shot_pawn.py -- <out.png> [eevee|cycles]
Everything is built here from scratch (no downloaded models): the pawn is a turned shape, like on a lathe.
"""
import math
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(args[0] if args else "test_pawn.png")
ENGINE = (args[1] if len(args) > 1 else "eevee").lower()

# ---------- a clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


# ---------- the pawn: a Staunton profile, turned (radius, height), height 1.0 ----------
PROFILE = [
    (0.000, 0.000), (0.300, 0.000), (0.312, 0.012), (0.315, 0.030), (0.305, 0.048), (0.282, 0.058),  # foot
    (0.276, 0.072), (0.262, 0.080), (0.250, 0.094), (0.238, 0.108),                                   # base bead
    (0.200, 0.128), (0.165, 0.160), (0.135, 0.215), (0.112, 0.300), (0.098, 0.390), (0.092, 0.450),   # stem
    (0.150, 0.470), (0.172, 0.482), (0.176, 0.494), (0.168, 0.506), (0.120, 0.520), (0.100, 0.532),   # collar
    (0.105, 0.548), (0.135, 0.578), (0.168, 0.625), (0.185, 0.680), (0.183, 0.735), (0.168, 0.790),   # head
    (0.140, 0.838), (0.100, 0.873), (0.055, 0.893), (0.000, 0.900),
]


def turned(name, profile, segments=128, scale=1.0):
    """A solid of revolution from a (radius, height) profile, smooth-shaded."""
    verts, faces = [], []
    n = len(profile)
    for s in range(segments):
        a = 2 * math.pi * s / segments
        for r, z in profile:
            verts.append((r * scale * math.cos(a), r * scale * math.sin(a), z * scale))
    for s in range(segments):
        t = (s + 1) % segments
        for i in range(n - 1):
            faces.append((s * n + i, t * n + i, t * n + i + 1, s * n + i + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)  # the axis points meet
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.modifiers.new("smooth", "SUBSURF").levels = 1
    return obj


pawn = turned("pawn", PROFILE, scale=1.0)

# crystal: clear glass with a faint warm tint, a little dispersion-like roughness variation
glass, nodes, links, bsdf = material("crystal")
bsdf.inputs["Base Color"].default_value = (0.98, 0.97, 0.95, 1)
bsdf.inputs["Roughness"].default_value = 0.02
bsdf.inputs["IOR"].default_value = 1.52
bsdf.inputs["Transmission Weight"].default_value = 1.0
glass.surface_render_method = "DITHERED"
try:
    glass.use_raytrace_refraction = True
except AttributeError:
    pass
pawn.data.materials.append(glass)

# ---------- the board: dark marble squares with fine veins, polished ----------
bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0, 0, 0))
board = bpy.context.active_object
marble, nodes, links, bsdf = material("marble")
tex = nodes.new("ShaderNodeTexCoord")
checker = nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 0.5  # one square = 1.0 wide (a checker cell is 1 / (2 x scale))
checker.inputs["Color1"].default_value = (0.020, 0.018, 0.017, 1)
checker.inputs["Color2"].default_value = (0.62, 0.60, 0.56, 1)
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 3.0
noise.inputs["Detail"].default_value = 12.0
wave = nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 1.6
wave.inputs["Distortion"].default_value = 9.0
wave.inputs["Detail"].default_value = 8.0
veins = nodes.new("ShaderNodeValToRGB")
veins.color_ramp.elements[0].position = 0.80
veins.color_ramp.elements[0].color = (1, 1, 1, 1)
veins.color_ramp.elements[1].position = 0.98
veins.color_ramp.elements[1].color = (0.55, 0.52, 0.48, 1)
mix = nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.blend_type = "MULTIPLY"
mix.inputs["Factor"].default_value = 0.65
links.new(tex.outputs["Object"], checker.inputs["Vector"])
links.new(tex.outputs["Object"], noise.inputs["Vector"])
links.new(noise.outputs["Color"], wave.inputs["Vector"])
links.new(wave.outputs["Fac"], veins.inputs["Fac"])
links.new(checker.outputs["Color"], mix.inputs[6])
links.new(veins.outputs["Color"], mix.inputs[7])
links.new(mix.outputs[2], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.08
try:
    bsdf.inputs["Coat Weight"].default_value = 0.6
    bsdf.inputs["Coat Roughness"].default_value = 0.03
except KeyError:
    pass
board.data.materials.append(marble)
pawn.location = (0.5, 0.5, 0.0)  # the middle of one square

# ---------- light: a soft key from the side, a rim behind, a faint studio world ----------
world = bpy.data.worlds.new("world")
scene.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
env = wn.new("ShaderNodeTexEnvironment")
studio = os.path.join(os.path.dirname(bpy.app.binary_path), f"{bpy.app.version[0]}.{bpy.app.version[1]}",
                      "datafiles", "studiolights", "world", "studio.exr")
if os.path.exists(studio):
    env.image = bpy.data.images.load(studio)
    wl.new(env.outputs["Color"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.25


def area(name, loc, rot, power, size, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size, light.color = power, size, color
    obj = bpy.data.objects.new(name, light)
    obj.location, obj.rotation_euler = loc, [math.radians(v) for v in rot]
    scene.collection.objects.link(obj)


area("key", (-2.6, -1.6, 2.4), (55, 0, -58), 420, 1.6, (1.0, 0.93, 0.84))
area("rim", (1.8, 3.2, 1.6), (-65, 0, 150), 650, 0.6, (0.75, 0.85, 1.0))
area("fill", (2.5, -2.5, 0.8), (80, 0, 45), 60, 3.0)

# a soft, warm backdrop far behind the pawn: glass shows what's behind it, so it needs light there to glow
bpy.ops.mesh.primitive_plane_add(size=14, location=(3.5, 6.5, 2.5), rotation=(math.radians(90), 0, math.radians(-35)))
back = bpy.context.active_object
glow, gn, gl, gb = material("backdrop")
grad = gn.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
coord = gn.new("ShaderNodeTexCoord"); mapn = gn.new("ShaderNodeMapping")
mapn.inputs["Scale"].default_value = (0.16, 0.16, 0.16)
gl.new(coord.outputs["Object"], mapn.inputs["Vector"]); gl.new(mapn.outputs["Vector"], grad.inputs["Vector"])
ramp = gn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1); ramp.color_ramp.elements[1].color = (0.55, 0.42, 0.28, 1)
gl.new(grad.outputs["Fac"], ramp.inputs["Fac"])
gb.inputs["Base Color"].default_value = (0, 0, 0, 1)
gl.new(ramp.outputs["Color"], gb.inputs["Emission Color"]); gb.inputs["Emission Strength"].default_value = 1.6
back.data.materials.append(glow)

# ---------- camera: low, close, shallow focus on the pawn ----------
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 85
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 1.8
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0.5 - 2.6, 0.5 - 3.4, 0.62)
target = bpy.data.objects.new("target", None)
target.location = (0.5, 0.5, 0.42)
scene.collection.objects.link(target)
cam_data.dof.focus_object = target
track = cam.constraints.new("TRACK_TO")
track.target, track.track_axis, track.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"

# ---------- render ----------
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
if ENGINE == "cycles":
    scene.render.engine = "CYCLES"
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
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    ee = scene.eevee
    for attr, value in (("use_raytracing", True), ("taa_render_samples", 64), ("use_shadows", True),
                        ("ray_tracing_method", "SCREEN"), ("use_gtao", True)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, value)
            except (TypeError, ValueError):
                pass
bpy.ops.render.render(write_still=True)
print("SAVED", OUT, scene.render.engine)
