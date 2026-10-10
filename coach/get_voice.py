"""Download the coach's voice (Kokoro v1.0, Apache-2.0) into voice/.

Run:  python -m coach.get_voice
Source: github.com/thewh1teagle/kokoro-onnx releases (model-files-v1.0): about 120 MB in total.
"""
import urllib.request

from coach.voice import MODEL, VOICES

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


def main():
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    for target in (MODEL, VOICES):
        if target.exists():
            print(f"already there: {target.name}")
            continue
        print(f"downloading {target.name} ...")
        urllib.request.urlretrieve(BASE + target.name, target)
    print(f"voice ready in {MODEL.parent}")


if __name__ == "__main__":
    main()
