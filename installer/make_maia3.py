"""Makes engine/maia3/maia3-5m.npz, the human-move model's weights, from Maia-3's own checkpoint. No PyTorch needed.

Run once by the maintainer (python installer/make_maia3.py); players get the .npz inside the app. The checkpoint is
UofTCSSLab/Maia3-5M on Hugging Face (21 MB, AGPL-3.0, github.com/CSSLab/maia3). A PyTorch checkpoint is a zip of
raw numbers plus a pickle that says how they fit together; only those few known names are allowed through here
(like torch.load(weights_only=True)), so the file can't run any code.

20 Oct 2026: PyTorch itself is blocked on the developer's PC by Windows' Smart App Control, so Knightwise runs the
model in numpy (coach/maia.py) and this reads the weights without it.
"""
import io
import pickle
import sys
import urllib.request
import zipfile
from collections import OrderedDict
from pathlib import Path

import numpy as np

URL = "https://huggingface.co/UofTCSSLab/Maia3-5M/resolve/main/maia3-5m.pt"
OUT = Path(__file__).resolve().parent.parent / "engine" / "maia3" / "maia3-5m.npz"
DTYPES = {"FloatStorage": np.float32, "HalfStorage": np.float16, "BFloat16Storage": None, "LongStorage": np.int64,
          "IntStorage": np.int32, "BoolStorage": np.bool_, "DoubleStorage": np.float64}


def _rebuild(storage, offset, size, stride, *_):
    data, = storage
    if not size:
        return data[offset:offset + 1].reshape(())
    item = data.itemsize
    return np.lib.stride_tricks.as_strided(data[offset:], shape=tuple(size), strides=[s * item for s in stride]).copy()


class _Storage:
    def __init__(self, name):
        self.name = name


def read(raw):
    """{name: numpy array} from a PyTorch checkpoint's bytes."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    root = z.namelist()[0].split("/")[0]

    class Safe(pickle.Unpickler):
        def find_class(self, module, name):
            if (module, name) in (("torch._utils", "_rebuild_tensor_v2"), ("torch._utils", "_rebuild_tensor")):
                return _rebuild
            if (module, name) == ("torch._utils", "_rebuild_parameter"):
                return lambda t, *_: t
            if module == "torch" and name in DTYPES:
                return _Storage(name)
            if (module, name) == ("collections", "OrderedDict"):
                return OrderedDict
            raise pickle.UnpicklingError(f"not allowed in a weights file: {module}.{name}")

        def persistent_load(self, pid):
            _, kind, key, _location, _numel = pid
            dtype = DTYPES[kind.name]
            if dtype is None:  # bfloat16: the top half of a float32
                b = np.frombuffer(z.read(f"{root}/data/{key}"), dtype=np.uint16).astype(np.uint32) << 16
                return (b.view(np.float32),)
            return (np.frombuffer(z.read(f"{root}/data/{key}"), dtype=dtype),)

    obj = Safe(io.BytesIO(z.read(f"{root}/data.pkl"))).load()
    state = obj["model_state_dict"] if isinstance(obj, dict) and "model_state_dict" in obj else obj
    return {k.replace("smolgen", "gab"): np.asarray(v, dtype=np.float32) for k, v in state.items()
            if isinstance(v, np.ndarray)}


def main(path=None):
    raw = Path(path).read_bytes() if path else urllib.request.urlopen(URL, timeout=300).read()
    weights = read(raw)
    for k in [k for k in weights if k.endswith(".self_attn.gab_weight")]:  # each layer holds the shared one: keep it once
        assert np.array_equal(weights[k], weights["gab_shared_weight"]), k
        del weights[k]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, **weights)
    print(f"{len(weights)} weights, {sum(w.size for w in weights.values()):,} numbers -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
