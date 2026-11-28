"""Every script of the app and the extension parses (28 Nov: a name declared twice in app.js broke every page at once;
the UI check caught it, but only when run by hand). Node is on the owner's PC and on GitHub's test machine."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted(list((ROOT / "coach" / "ui").glob("*.js")) + list((ROOT / "extension").glob("*.js")))


@pytest.mark.skipif(not shutil.which("node"), reason="Node isn't installed")
@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_parses(script):
    r = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr.strip()[-600:]
