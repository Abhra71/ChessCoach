"""28 Nov, the owner: "a lot of things seem to be missing" (a game resigned while winning). In the real page: the last
move says where you really stood, the game's report comes back as a wrap-up, and "Play on" opens a game you can play.
Uses the first game in your data that was given up while it wasn't lost (skipped if there is none)."""
import json
import urllib.request

import pytest

from tests.ui.conftest import PROJECT, URL

SHOTS = PROJECT / "logbook" / "ui-check"


def _given_up_game():
    games = json.loads(urllib.request.urlopen(URL + "/api/games", timeout=30).read())
    for g in games:
        if g.get("checked") and g.get("result") != "win" and g.get("how") in ("resigned", "timeout", "abandoned"):
            d = json.loads(urllib.request.urlopen(f"{URL}/api/games/{g['id']}", timeout=60).read())
            if (d.get("the_end") or {}).get("play_on"):
                return d
    return None


def test_the_end_of_a_game_given_up_while_not_lost(app, browser):
    d = _given_up_game()
    if not d:
        pytest.skip("no game given up while it wasn't lost in this data")
    ctx = browser.new_context(viewport={"width": 1400, "height": 1000})
    ctx.add_init_script("try { localStorage.setItem('kw-music-muted', '1') } catch (e) {}")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    try:
        page.goto(f"{URL}/app#/games/{d['id']}", wait_until="networkidle", timeout=30_000)
        page.click("#startreview")
        page.keyboard.press("End")  # the last move
        page.wait_for_timeout(600)
        text = page.inner_text("#walk")
        if "The end:" not in text:  # End didn't jump: step with the last-move button
            page.locator("button").filter(has_text="⏭").first.click()
            page.wait_for_timeout(600)
            text = page.inner_text("#walk")
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / "review-the-end.png"))
        assert d["the_end"]["say"] in text, text
        assert "Accuracy" not in text, "the report is the cover page only (owner, 28 Nov)"
        page.click("text=Play on from")
        page.wait_for_selector(".rstart", timeout=30_000)
        page.wait_for_timeout(4000)  # the lead-in
        assert "where the game ended" in page.inner_text("#page")
        page.screenshot(path=str(SHOTS / "play-on.png"))
        assert not errors, errors
    finally:
        ctx.close()
