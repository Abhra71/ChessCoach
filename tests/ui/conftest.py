"""Shared by the UI checks (check-ui.bat): a private copy of Knightwise and the PC's own Edge, hidden and muted.

The private copy runs on its own port with a copy of data/ (your games; voice and sounds off, no AI keys), never the
Store app. A normal test run skips all of this (KNIGHTWISE_UI=1 turns it on)."""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / "data"
PORT = 8799
URL = f"http://127.0.0.1:{PORT}"


def pytest_collection_modifyitems(config, items):
    if os.environ.get("KNIGHTWISE_UI") != "1":
        skip = pytest.mark.skip(reason="the UI check runs on its own: check-ui.bat")
        for item in items:
            if "tests" in item.path.parts and "ui" in item.path.parts:
                item.add_marker(skip)


def _get(path, timeout=3):
    return json.loads(urllib.request.urlopen(URL + path, timeout=timeout).read())


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """A private copy of the app with a copy of your data, on its own port; closed at the end."""
    if not (DATA / "player.txt").exists():
        pytest.skip("no data/ folder with a player to show")
    home = tmp_path_factory.mktemp("ui-home")
    shutil.copytree(DATA, home / "data", ignore=shutil.ignore_patterns("voice-cache", "service.pid"))
    settings = home / "data" / "settings.json"
    s = json.loads(settings.read_text()) if settings.exists() else {}
    s.update({"voice": False, "sounds": False})
    for slot in ("slot1", "slot2"):
        s.pop(slot, None)
    settings.write_text(json.dumps(s))
    env = dict(os.environ, KNIGHTWISE_HOME=str(home), KNIGHTWISE_PORT=str(PORT), KNIGHTWISE_VAULT="Knightwise-uicheck")
    proc = subprocess.Popen([sys.executable, "-c", "from coach import service; service.start(); import time; time.sleep(10**6)"],
                            cwd=PROJECT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):  # up to a minute for the coach to start
            try:
                _get("/api/status")
                break
            except OSError:
                time.sleep(0.5)
        else:
            pytest.fail("the private copy of the app didn't start")
        yield home
    finally:  # the whole tree: its game-checking helpers too (28 Nov: 16 were left behind, idle, after test runs)
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        proc.kill()
        proc.wait(timeout=10)


@pytest.fixture(scope="session")
def browser():
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="msedge", headless=True, args=["--mute-audio"])
        except Exception as e:  # no Edge on this machine
            pytest.skip(f"Microsoft Edge not available: {e}")
        yield b
        b.close()
