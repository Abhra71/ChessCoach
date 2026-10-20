"""Download the 3D welcome scene: Poly Haven "Chess Set" (CC0, by Riley Queen, ~20 MB) and Three.js (MIT, ~1.5 MB),
and its music: Satie's Gymnopedie No. 1 played by Michael Laucke (public domain, Wikimedia Commons, ~10 MB).
The film of your game (1.0) plays one of two songs the owner picked by ear on 20 Oct 2026, both CC BY 3.0 from
ccMixter (credited in Settings → About and credits): "Time has come" by Reiswerk feat. SackJo22 (with parts by
SackJo22 and Apoxode, 9 MB) and "A Trio Cultural Mix (instrumental)" by CSoul (samples by debbizo, 2 MB).

Run:  python -m coach.get_assets      (files go to coach/ui/vendor/, kept out of git; the installer bundles them)
"""
import json
import urllib.request

from coach.paths import TEMPLATES

VENDOR = TEMPLATES / "ui" / "vendor"
THREE = "0.186.1"
THREE_FILES = {  # published path in the three package -> local name
    "build/three.module.min.js": "three.module.min.js",
    "build/three.core.min.js": "three.core.js",  # three.module.min.js imports it as ./three.core.js
    "examples/jsm/loaders/GLTFLoader.js": "addons/loaders/GLTFLoader.js",
    "examples/jsm/utils/BufferGeometryUtils.js": "addons/utils/BufferGeometryUtils.js",
    "examples/jsm/utils/SkeletonUtils.js": "addons/utils/SkeletonUtils.js",
    "examples/jsm/environments/RoomEnvironment.js": "addons/environments/RoomEnvironment.js",
    # depth of field (the background softly out of focus)
    "examples/jsm/postprocessing/EffectComposer.js": "addons/postprocessing/EffectComposer.js",
    "examples/jsm/postprocessing/Pass.js": "addons/postprocessing/Pass.js",
    "examples/jsm/postprocessing/RenderPass.js": "addons/postprocessing/RenderPass.js",
    "examples/jsm/postprocessing/ShaderPass.js": "addons/postprocessing/ShaderPass.js",
    "examples/jsm/postprocessing/MaskPass.js": "addons/postprocessing/MaskPass.js",
    "examples/jsm/postprocessing/BokehPass.js": "addons/postprocessing/BokehPass.js",
    "examples/jsm/postprocessing/OutputPass.js": "addons/postprocessing/OutputPass.js",
    "examples/jsm/shaders/CopyShader.js": "addons/shaders/CopyShader.js",
    "examples/jsm/shaders/BokehShader.js": "addons/shaders/BokehShader.js",
    "examples/jsm/shaders/OutputShader.js": "addons/shaders/OutputShader.js",
}
MUSIC = ("https://upload.wikimedia.org/wikipedia/commons/a/a6/Satie_Gymnopedie_No_1_performed_by_Michael_Laucke.flac",
         "music/gymnopedie-1.flac")
AGENT = {"User-Agent": "Knightwise (github.com/Abhra71/ChessCoach)"}
# (address, file, the track's own page): ccMixter only gives the file to a request that comes from its page
FILM_SONGS = [
    ("https://ccmixter.org/content/Reiswerk/Reiswerk_-_Time_has_come_feat_Sackjo22.mp3", "film/time-has-come.mp3",
     "https://ccmixter.org/files/Reiswerk/51212"),
    ("https://ccmixter.org/content/CSoul/CSoul_-_A_Trio_Cultural_Mix_Instrumental_Version.mp3", "film/trio-cultural-mix.mp3",
     "https://ccmixter.org/files/CSoul/32315"),
]


def fetch(url, target, page=None):
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    head = {**AGENT, "Referer": page} if page else AGENT
    with urllib.request.urlopen(urllib.request.Request(url, headers=head), timeout=120) as resp:
        data = resp.read()
    if len(data) < 10_000 and page:  # a refusal ("Forbidden"), not a song
        raise RuntimeError(f"{url} refused the download; get it from {page}")
    target.write_bytes(data)


def main():
    for src, dst in THREE_FILES.items():
        fetch(f"https://cdn.jsdelivr.net/npm/three@{THREE}/{src}", VENDOR / "three" / dst)
    files = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.polyhaven.com/files/chess_set", headers=AGENT), timeout=60))["gltf"]["2k"]["gltf"]
    folder = VENDOR / "chess_set"
    fetch(files["url"], folder / "chess_set_2k.gltf")
    for rel, info in files["include"].items():
        fetch(info["url"], folder / rel)
    fetch(MUSIC[0], VENDOR / MUSIC[1])
    for url, dst, page in FILM_SONGS:
        fetch(url, VENDOR / dst, page)
    print(f"3D scene ready in {VENDOR}")


if __name__ == "__main__":
    main()
