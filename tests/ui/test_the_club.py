"""The club in the real app (storyline 3.3 to 3.6): a chess word is underlined and a tap (a click, not a hover) shows
its meaning; each page shows its room; Explore answers a chess word; In your head brings Viktor's regret, once."""
from tests.ui.conftest import URL


def _page(browser):
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    return page, errors


def test_a_tap_explains_a_chess_word(app, browser):
    page, errors = _page(browser)
    try:
        page.goto(f"{URL}/app#/progress", wait_until="networkidle", timeout=30_000)
        page.wait_for_selector("#page .term", timeout=15_000)
        assert page.locator(".room").first.inner_text().strip().lower() == "your record"
        term = page.locator("#page .term").first
        word = term.get_attribute("data-word")
        term.click()
        pop = page.locator(".term-pop")
        pop.wait_for(timeout=3000)
        assert word in pop.inner_text() and len(pop.inner_text()) > len(word) + 10
        page.mouse.click(5, 790)  # anywhere else closes it
        page.wait_for_timeout(200)
        assert page.locator(".term-pop").count() == 0
        assert not errors, errors
    finally:
        page.close()


def test_explore_answers_a_chess_word_and_the_words_page_lists_all(app, browser):
    page, errors = _page(browser)
    try:
        page.goto(f"{URL}/app#/plan", wait_until="networkidle", timeout=30_000)
        page.fill("#xq", "zugzwang")
        page.wait_for_selector(".xword", timeout=5000)
        assert "Any move makes it worse" in page.locator(".xword").first.inner_text()
        page.goto(f"{URL}/app#/words", wait_until="networkidle")
        page.wait_for_selector("#wl .word")
        assert page.locator("#wl .word").count() == 33
        page.fill("#wq", "fork")
        page.wait_for_timeout(200)
        assert page.locator("#wl .word:visible").count() >= 1
        page.goto(f"{URL}/app#/coaches", wait_until="networkidle")
        page.wait_for_selector(".meet-card")
        assert page.locator(".meet-card").count() == 2 and "Berlin" in page.inner_text("#page")
        assert not errors, errors
    finally:
        page.close()


def test_viktors_regret_comes_once_in_your_head(app, browser):
    page, errors = _page(browser)
    try:
        import json
        told = json.loads((app / "data" / "story.json").read_text()).get("told_lines", {})             if (app / "data" / "story.json").exists() else {}
        page.goto(f"{URL}/app#/calc", wait_until="networkidle", timeout=30_000)
        if "viktor-regret" in told:  # the page check opened In your head first: it was told then, once
            assert "a move I didn't check" not in page.inner_text("body")
        else:
            page.wait_for_function("document.body.innerText.includes(\"a move I didn't check\")", timeout=20_000)
            assert page.locator(".kw-head").first.inner_text().startswith("Viktor")
        page.goto(f"{URL}/app#/train", wait_until="networkidle")
        page.goto(f"{URL}/app#/calc", wait_until="networkidle")
        page.wait_for_timeout(3000)
        assert "a move I didn't check" not in page.inner_text("body")
        assert not errors, errors
    finally:
        page.close()
