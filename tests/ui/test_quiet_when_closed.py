"""28 Nov, the owner: "a coach is saying something and I close the app, the coach still continues to say, and I could
hear sound of badges even when the app is closed." Closing only hides the window, so the page must go silent itself.
This plays real sounds in the real page (in a muted Edge), "closes" the window as coach/app.py does, and listens."""
from tests.ui.conftest import URL


def test_closing_silences_everything_and_music_comes_back(app, browser):
    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        page.goto(f"{URL}/app#/home", wait_until="networkidle", timeout=30_000)
        page.evaluate("""() => {
            window.t_song = new Audio('/ui/sounds/move.ogg'); t_song.loop = true; t_song.play();
            window.t_word = new Audio('/ui/sounds/move.ogg'); t_word.play();
        }""")
        page.wait_for_timeout(200)
        assert page.evaluate("!t_song.paused")
        page.evaluate("kwAway(true)")  # what coach/app.py calls when the window closes or is minimised
        assert page.evaluate("t_song.paused && t_word.paused"), "something kept playing after closing"
        refused = page.evaluate("""async () => {
            const a = new Audio('/ui/sounds/move.ogg');
            try { await a.play(); return false; } catch (e) { return e.name === 'NotAllowedError' && a.paused; }
        }""")
        assert refused, "a new sound (a badge, a voice line) could start while closed"
        assert page.evaluate("kwChime() === undefined && KW_AWAY")  # the badge chime returns at once
        page.evaluate("kwAway(false)")  # the window is back
        page.wait_for_timeout(200)
        assert page.evaluate("!t_song.paused"), "the music didn't come back with the window"
        assert page.evaluate("t_word.paused"), "a half-said line shouldn't restart"
    finally:
        ctx.close()
