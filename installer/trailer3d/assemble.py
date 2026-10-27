"""Trailer 2 ("Refined"): the 3D shots, the app's quick flashes, the words, the music and the maker's name, cut
together in Blender's video editor and saved as an MP4 (H.264 + AAC, what the Microsoft Store and YouTube take).

Run:  blender -b --factory-startup -P installer/trailer3d/assemble.py -- <root> <out.mp4> <music> <logo>
  root: the folder with frames/<shot>/ and flashes/ (from scene.py and prep_flashes.py)
"""
import glob
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT, MUSIC, LOGO = args[:4]
CREATOR = "Abhra Chakraborty"  # the owner's full name, at the very end (27 Oct)
FPS = 24
FONT_LIGHT = r"C:\Windows\Fonts\segoeuil.ttf"
FONT_BOLD = r"C:\Windows\Fonts\seguisb.ttf"

scene = bpy.context.scene
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1920, 1080, 100
# "Standard": the frames already have their film look from scene.py; AgX again would grey the words and app screens
scene.view_settings.view_transform, scene.view_settings.look = "Standard", "None"
ed = scene.sequence_editor_create()
STRIPS = ed.strips if hasattr(ed, "strips") else ed.sequences  # Blender 5: "strips"
font_light = bpy.data.fonts.load(FONT_LIGHT)
font_bold = bpy.data.fonts.load(FONT_BOLD)


def sec(s):
    return int(round(s * FPS)) + 1


def fade(strip, start, end, inn=0.4, out=0.4, peak=1.0):
    """Opacity up at the start and down at the end (seconds)."""
    pts = [(start, 0.0), (start + inn, peak), (end - out, peak), (end, 0.0)] if inn or out else []
    for t, v in pts:
        strip.blend_alpha = v
        strip.keyframe_insert("blend_alpha", frame=sec(t))


def shot(name, start, channel=1, inn=0.5, out=0.5, skip=0.0, take=None):
    """A 3D shot from `start`; skip: seconds left out at its start; take: at most this many seconds of it."""
    files = sorted(glob.glob(os.path.join(ROOT, "frames", name, f"{name}_*.png")))
    files = files[int(skip * FPS):]
    if take:
        files = files[:int(take * FPS)]
    if not files:
        print("MISSING", name)
        return start
    s = STRIPS.new_image(name, files[0], channel, sec(start))
    for f in files[1:]:
        s.elements.append(os.path.basename(f))
    s.blend_type = "ALPHA_OVER"
    end = start + len(files) / FPS
    fade(s, start, end, inn, out)
    return end


def flash(file, start, length, zoom=(1.0, 1.06), channel=1):
    """An app screen for a moment, drifting closer, cut hard (no fades): quick and bright between the dark shots."""
    s = STRIPS.new_image(os.path.basename(file), os.path.join(ROOT, "flashes", file), channel, sec(start))
    s.frame_final_duration = int(round(length * FPS))
    s.blend_type = "ALPHA_OVER"
    tr = s.transform
    for t, z in ((start, zoom[0]), (start + length, zoom[1])):
        tr.scale_x = tr.scale_y = z
        tr.keyframe_insert("scale_x", frame=sec(t))
        tr.keyframe_insert("scale_y", frame=sec(t))
    return start + length


def words(text, start, end, size=64, y=0.14, font=None, colour=(0.96, 0.94, 0.90, 1), channel=6, inn=0.6, out=0.6,
          box=False):
    if end - start < 0.3:  # its shot isn't there (not rendered yet): no line rather than a broken cut
        print("SKIPPED words:", text)
        return None
    t = STRIPS.new_effect(f"t_{start}", "TEXT", channel, frame_start=sec(start), length=sec(end) - sec(start))
    if box:  # a caption over an app screen: on a dark band, so it reads over anything
        t.use_box, t.box_color, t.box_margin = True, (0.02, 0.02, 0.02, 0.82), 0.018
    t.text, t.font_size, t.color = text, size, colour
    t.font = font or font_light
    t.location = (0.5, y)
    t.anchor_x, t.anchor_y = "CENTER", "CENTER"
    t.use_shadow, t.shadow_color = True, (0, 0, 0, 0.9)
    t.blend_type = "ALPHA_OVER"
    fade(t, start, end, inn, out)
    return t


def black(start, end, channel=1):
    c = STRIPS.new_effect(f"black_{start}", "COLOR", channel, frame_start=sec(start), length=sec(end) - sec(start))
    c.color = (0, 0, 0)
    return c


# ---------- the cut (seconds) ----------
black(0, 70, channel=1)  # everything sits on black: fades go to black, not to grey
t = shot("above", 0.0, channel=2, inn=1.0)  # wide, from above: the whole board
words("Every game has a story.", 1.2, 4.6)
t = shot("reveal", t, channel=3, skip=1.6, take=4.0, inn=0.4)
r0 = t
t = shot("rank", t, channel=2, skip=1.0, take=4.0, inn=0.4)
words("Some moves cost more than you think.", r0 + 0.3, t - 0.3)
t = shot("blunder", t, channel=3, out=0.3)
words("Knightwise finds them.", t + 0.1, t + 1.9, size=78, y=0.5, font=font_bold, inn=0.25, out=0.3)
t += 2.0
# the big features, one each, with a line: what the app is, not every button in it
FEATURES = [("03-home.png", "Two coaches who talk you through every game"),
            ("02-review.png", "Every move reviewed, and the better one shown"),
            ("04-practice.png", "Practice made from your own mistakes"),
            ("08-guess.png", "Opponents that play like real people"),
            ("05-train.png", "Train: endgames, blindfold, seeing ahead"),
            ("07-level.png", "Your level, from beginner to 2,000")]
for f, line in FEATURES:
    words(line, t + 0.05, t + 1.95, size=50, y=0.10, font=font_bold, inn=0.15, out=0.15, box=True)
    t = flash(f, t, 2.0, channel=4)
c0 = t
t = shot("cradle", t, channel=2, skip=0.6, take=6.0, inn=0.3)
words("And trains you, move by move.", c0 + 1.0, c0 + 5.0)
t = shot("mate", t, channel=3, inn=0.3, out=0.4)
f0 = t
t = shot("rise", t, channel=2, inn=0.4, out=1.0)  # wide again: a whole crystal game from above
words("Fair.  Free.  Yours.", f0 + 0.6, t - 0.4, size=72)
# the end: the knight, the name of the app, where to get it; then the one who made it
end0 = t + 0.3
logo = STRIPS.new_image("logo", LOGO, 3, sec(end0))
logo.frame_final_duration = int(4.2 * FPS)
logo.blend_type = "ALPHA_OVER"
logo.transform.scale_x = logo.transform.scale_y = 0.12
logo.transform.offset_y = 120
fade(logo, end0, end0 + 4.2, 0.8, 0.6)
words("Knightwise", end0 + 0.3, end0 + 4.2, size=96, y=0.40, font=font_bold, inn=0.8)
words("Free on the Microsoft Store", end0 + 1.0, end0 + 4.2, size=58, y=0.30, font=font_bold, colour=(0.88, 0.70, 0.36, 1), inn=0.8)
name0 = end0 + 4.4
words("DEVELOPED BY", name0, name0 + 4.4, size=30, y=0.56, font=font_bold, colour=(0.88, 0.70, 0.36, 1), inn=0.7, out=0.8)
# the name, rubbed into view left to right in Palatino (frames from name_reveal.py); plain words if they're missing
if not shot("name", name0 + 0.3, channel=7, inn=0.05, out=0.8) > name0 + 0.3:
    words(CREATOR, name0 + 0.3, name0 + 4.4, size=110, y=0.46, font=font_light, inn=0.9, out=0.8)
LENGTH = name0 + 4.9

# ---------- the music: calm, in and out ----------
music = STRIPS.new_sound("music", MUSIC, 8, sec(0))
for tt, v in ((0, 0.0), (1.5, 0.85), (LENGTH - 3.5, 0.85), (LENGTH - 0.2, 0.0)):
    music.volume = v
    music.keyframe_insert("volume", frame=sec(tt))

scene.frame_start, scene.frame_end = 1, sec(LENGTH)
if os.environ.get("KW_RANGE"):  # a quick check of part of the cut: "start,end" in seconds, saved as stills
    a0, a1 = (float(x) for x in os.environ["KW_RANGE"].split(","))
    for tt in (a0, (a0 + a1) / 2, a1):
        scene.frame_set(sec(tt))
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = f"{OUT}_check_{tt:05.1f}.png"
        bpy.ops.render.render(write_still=True)
    print("LENGTH", round(LENGTH, 1))
    raise SystemExit(0)
r = scene.render
if hasattr(r.image_settings, "media_type"):  # Blender 5: video is its own kind of output
    r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format, r.ffmpeg.codec = "MPEG4", "H264"
r.ffmpeg.constant_rate_factor, r.ffmpeg.ffmpeg_preset = "HIGH", "GOOD"
r.ffmpeg.audio_codec, r.ffmpeg.audio_bitrate, r.ffmpeg.audio_channels = "AAC", 192, "STEREO"
r.use_sequencer = True
r.filepath = OUT
bpy.ops.render.render(animation=True)
print("DONE", OUT, round(LENGTH, 1), "s")
