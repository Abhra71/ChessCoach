"""Download the 3D welcome scene: Poly Haven "Chess Set" (CC0, by Riley Queen, ~20 MB) and Three.js (MIT, ~1.5 MB),
and its music: Satie's Gymnopedie No. 1 played by Michael Laucke (public domain, Wikimedia Commons, ~10 MB).

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


def fetch(url, target):
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=120) as resp:
        target.write_bytes(resp.read())


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
    print(f"3D scene ready in {VENDOR}")


if __name__ == "__main__":
    main()
