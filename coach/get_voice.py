"""Download the coach's voice (Kokoro v1.0, Apache-2.0) into voice/.

Run:  python -m coach.get_voice
Sources: github.com/thewh1teagle/kokoro-onnx releases (model-files-v1.0, ~120 MB, Apache-2.0) for speaking,
huggingface.co/Systran/faster-whisper-small.en (~485 MB, MIT) for listening.
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
    print("downloading the listening model (Whisper small.en, ~485 MB) ...")
    download_hearing()
    print("listening ready")



HEARING = "https://huggingface.co/Systran/faster-whisper-small.en/resolve/main/"
HEARING_FILES = ("config.json", "tokenizer.json", "vocabulary.txt", "model.bin")  # ~485 MB, MIT


def download_hearing(progress=None):
    """Whisper small.en for the coach to hear questions. progress(done_bytes, total_bytes) while downloading."""
    from coach.hearing import MODEL_DIR
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name in HEARING_FILES:
        target = MODEL_DIR / name
        if target.exists():
            continue
        part = target.with_suffix(target.suffix + ".part")
        req = urllib.request.Request(HEARING + name, headers={"User-Agent": "ChessCoach"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(part, "wb") as fh:
            total, done = int(resp.headers.get("Content-Length", 0)), 0
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
        part.replace(target)  # only complete files count


if __name__ == "__main__":
    main()
