"""The UI department (28 Nov): opens every page of the app in a real browser, like a player, and checks it.

What it catches: JavaScript errors, server errors behind a page, a page that comes up empty, and sideways scrolling
(something wider than the window). It saves a screenshot of every page to logbook/ui-check/ so a person (or Claude)
can look at them all at once. The private app and the browser come from tests/ui/conftest.py.

Run it with check-ui.bat. A normal test run skips it (it needs Edge and a data/ folder, and takes about a minute).
"""
import pytest

from tests.ui.conftest import PROJECT, URL

SHOTS = PROJECT / "logbook" / "ui-check"

# Every page in the side menu and the tools behind Train and Your plan (coach/ui/app.js, NAMES).
PAGES = ["home", "games", "practice", "daily", "plan", "course", "level", "progress", "train", "openings",
         "repertoire", "blindfold", "guess", "endgames", "calc", "prep", "settings", "words", "coaches"]
SIZES = {"window": (1280, 800), "small": (1000, 680)}


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
