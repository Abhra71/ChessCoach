"""Trailer 2 ("Refined"): the 3D shots, the app's quick flashes, the words, the music and the maker's name, cut
together in Blender's video editor and saved as an MP4 (H.264 + AAC, what the Microsoft Store and YouTube take).

Run:  blender -b --factory-startup -P installer/trailer3d/assemble.py -- <root> <out.mp4> <music> <logo>
  root: the folder with frames/<shot>/ and flashes/ (from scene.py and prep_flashes.py)
"""
import glob
import math
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


# ---------- the cut (seconds): version 3, the app first; the 3D frames it (owner's notes, 27 Oct) ----------
font_serif = bpy.data.fonts.load(r"C:\Windows\Fonts\palab.ttf")
black(0, 80, channel=1)  # everything sits on black: fades go to black, not to grey
# the hook: the best shot, at once: the crystal king falling
t = shot("mate", 0.0, channel=2, skip=1.0, take=2.6, inn=0.15, out=0.3)
lg = STRIPS.new_image("hook_logo", LOGO, 3, sec(t))
lg.frame_final_duration = int(1.3 * FPS)
lg.blend_type, lg.transform.scale_x, lg.transform.scale_y = "ALPHA_OVER", 0.10, 0.10
lg.transform.offset_y = 70
fade(lg, t, t + 1.3, 0.2, 0.3)
words("Knightwise", t + 0.1, t + 1.3, size=84, y=0.40, font=font_bold, inn=0.2, out=0.3)
t += 1.4
# the problem: a mistake, in slow motion
b0 = t
t = shot("blunder", t, channel=2, inn=0.3, out=0.3)
words("Every lost game has a reason.", b0 + 1.4, t - 0.3, size=66, font=font_serif)
# the app, moving: each big feature as a real clip in a floating window. It slides in, the words are read, then the
# camera goes in close (pixel-sharp: the clip is full size), holds while the action plays, and comes back out. Each
# feature moves differently, so it never feels like the same zoom (owner's notes, 27 Oct)
S0 = 0.60                      # the window's size on screen (a full-size clip shown at 60%)
FEATURES = [  # clip, kicker, headline, line under it, close-up: [(scale, focus point on the 1920x1080 clip, where on screen)], turn
    ("home", "YOUR COACHES", "Two coaches, always with you", "They go through every game with you, out loud",
     [(0.92, (1250, 640), (0, 0)), (0.96, (1330, 690), (0, 0))], 0),              # the game opening, Maya talking
    ("review", "GAME REVIEW", "Every move, reviewed", "The moments that cost you, and the better move",
     [(0.88, (900, 520), (-60, 0)), (0.88, (1480, 430), (-20, 10))], 0),          # the board, then across to the panel
    ("practice", "PRACTICE", "Practice from your mistakes", "Your positions come back until you get them right",
     [(0.86, (1100, 420), (0, 0)), (0.92, (950, 410), (40, 10))], 0),              # a slow drift in: the move and the "right"
    ("guess", "HUMAN-LIKE", "Opponents who play like people", "A model of human chess, not a perfect engine",
     [(0.90, (1100, 560), (0, 0)), (0.92, (1180, 560), (20, 0))], -1.5),          # with a slight turn
    ("train", "TRAIN", "Train like a pro", "Endgames, blindfold, and seeing the whole line",
     [(0.95, (700, 560), (-40, -20)), (0.95, (1500, 560), (40, -20))], 0),        # tracking along the cards
    ("level", "YOUR LEVEL", "From beginner to 2,000", "Five steps, each measured in your own games",
     [(0.98, (1100, 260), (0, 60)), (0.80, (1100, 520), (0, 0))], 0),             # close on the steps, then easing back
]
EACH = 5.4
for i, (clip, kicker, head, line, close, turn) in enumerate(FEATURES):
    a0, a1 = t, t + EACH
    print("FEATURE", clip, round(a0, 2))
    bg = STRIPS.new_image(f"back{i}", os.path.join(ROOT, "cards", f"back{i}.png"), 2, sec(a0))
    bg.frame_final_duration = int(EACH * FPS)
    for tt, z in ((a0, 1.0), (a1, 1.06)):
        bg.transform.scale_x = bg.transform.scale_y = z
        bg.transform.keyframe_insert("scale_x", frame=sec(tt)); bg.transform.keyframe_insert("scale_y", frame=sec(tt))
    fade(bg, a0, a1, 0.25 if i else 0.4, 0.25)
    files = sorted(glob.glob(os.path.join(ROOT, "cards", f"clip_{clip}", f"clip_{clip}_*.png")))
    c = STRIPS.new_image(clip, files[0], 4, sec(a0), fit_method="ORIGINAL")
    for f in files[1:]:
        c.elements.append(os.path.basename(f))
    c.frame_final_duration = min(len(files), int(EACH * FPS))
    c.blend_type = "ALPHA_OVER"
    w = c.elements[0].orig_width or 2100
    base = 1920 / 2 - 20 - w * S0 / 2  # the window on the right, its words on the left
    tr = c.transform

    def at(tt, z, focus=None, screen=None, rot=0.0, slide=0.0):
        if focus:  # put this point of the clip at this place on the screen
            rx, ry = focus[0] - 960, 540 - focus[1]
            ox, oy = screen[0] - rx * z, screen[1] - ry * z
        else:
            ox, oy = base + slide, 0
        tr.scale_x = tr.scale_y = z
        tr.offset_x, tr.offset_y, tr.rotation = ox, oy, math.radians(rot)
        for k in ("scale_x", "scale_y", "offset_x", "offset_y", "rotation"):
            tr.keyframe_insert(k, frame=sec(tt))

    (z1, f1, p1), (z2, f2, p2) = close
    at(a0, S0, slide=120)              # slides in
    at(a0 + 0.5, S0)
    at(a0 + 2.3, S0 * 1.03)            # a slight drift while the words are read
    at(a0 + 3.0, z1, f1, p1, turn)     # in close
    at(a0 + 4.2, z2, f2, p2, turn)     # the hold, the clip playing (with a pan or a push, different each time)
    at(a0 + 4.85, S0)                  # and back out
    fade(c, a0, a1, 0.45, 0.3)
    for txt, y, size, font, col, d0, anchor in (
            (kicker, 0.64, 24, font_bold, (0.88, 0.70, 0.36, 1), 0.15, "BOTTOM"),
            (head, 0.605, 58, font_serif, (0.97, 0.95, 0.91, 1), 0.25, "TOP"),
            (line, 0.33, 30, font_light, (0.78, 0.76, 0.72, 1), 0.45, "TOP")):
        tx = words(txt, a0 + d0, a0 + 2.45, size=size, y=y, font=font, colour=col, inn=0.35, out=0.3)
        if tx:  # left-aligned in a column; the line under the headline sits well clear of its two lines
            tx.location = (0.055, y)
            tx.anchor_x, tx.anchor_y = "LEFT", anchor
            tx.use_shadow = False
            if hasattr(tx, "alignment_x"):
                tx.alignment_x = "LEFT"
            if hasattr(tx, "wrap_width"):
                tx.wrap_width = 0.27
    t = a1
# the promise, wide: a whole crystal game from above
f0 = t
t = shot("rise", t, channel=2, inn=0.4, out=1.0)
words("Fair.  Free.  Yours.", f0 + 0.6, t - 0.4, size=72, font=font_serif)
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
