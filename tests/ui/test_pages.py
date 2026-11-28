"""The UI department (28 Nov): opens every page of the app in a real browser, like a player, and checks it.

What it catches: JavaScript errors, server errors behind a page, a page that comes up empty, and sideways scrolling
(something wider than the window). It saves a screenshot of every page to logbook/ui-check/ so a person (or Claude)
can look at them all at once.

It runs a private copy of Knightwise on its own port with a copy of data/ (your games; voice and sounds off, no AI
keys), never the Store app. It drives the Microsoft Edge already on the PC (Playwright, Apache-2.0), hidden and muted.

Run it with check-ui.bat. A normal test run skips it (it needs Edge and a data/ folder, and takes about a minute).
"""
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
SHOTS = PROJECT / "logbook" / "ui-check"
PORT = 8799
URL = f"http://127.0.0.1:{PORT}"

# Every page in the side menu and the tools behind Train and Your plan (coach/ui/app.js, NAMES).
PAGES = ["home", "games", "practice", "daily", "plan", "course", "level", "progress", "train", "openings",
         "repertoire", "blindfold", "guess", "endgames", "calc", "prep", "settings"]
SIZES = {"window": (1280, 800), "small": (1000, 680)}

pytestmark = pytest.mark.skipif(os.environ.get("KNIGHTWISE_UI") != "1",
                                reason="the UI check runs on its own: check-ui.bat")


def _get(path, timeout=3):
    return json.loads(urllib.request.urlopen(URL + path, timeout=timeout).read())


@pytest.fixture(scope="module")
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
    finally:
        proc.kill()
        proc.wait(timeout=10)


@pytest.fixture(scope="module")
def browser():
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="msedge", headless=True, args=["--mute-audio"])
        except Exception as e:  # no Edge on this machine
            pytest.skip(f"Microsoft Edge not available: {e}")
        yield b
        b.close()


@pytest.mark.parametrize("size", list(SIZES))
@pytest.mark.parametrize("page_name", PAGES)
def test_page(app, browser, page_name, size):
    w, h = SIZES[size]
    ctx = browser.new_context(viewport={"width": w, "height": h})
    ctx.add_init_script("try { localStorage.setItem('kw-music-muted', '1') } catch (e) {}")
    page = ctx.new_page()
    problems = []
    page.on("pageerror", lambda e: problems.append(f"JavaScript error: {e}"))
    page.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource")
            and problems.append(f"console error: {m.text}"))  # failed loads are named below, with their address
    page.on("response", lambda r: r.status >= 400 and problems.append(f"missing or broken ({r.status}): {r.url}"))
    try:
        page.goto(f"{URL}/app#/{page_name}", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(1200)  # entrance animations
        text = page.inner_text("#page", timeout=5_000).strip() if page.query_selector("#page") else ""
        if len(text) < 20:
            problems.append(f"the page looks empty ({len(text)} characters of text)")
        wide = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        if wide > 1:
            problems.append(f"sideways scrolling: the page is {wide}px wider than the window")
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"{page_name}-{size}.png"), full_page=True)
    finally:
        ctx.close()
    assert not problems, f"{page_name} ({w}x{h}):\n  " + "\n  ".join(problems)
