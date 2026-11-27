"""The phone app's move rules (docs/app/rules.js) are tested in JavaScript; this runs those tests with the
rest, so `python -m pytest` covers them too. Skipped on a PC without Node.js."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_phone_app_rules():
    run = subprocess.run(["node", str(ROOT / "tests" / "mobile" / "rules_test.js")],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    assert " passed" in run.stdout
