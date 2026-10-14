import random

from coach import coaches, voice

HOME = {"player": "gushynanda", "games": 140, "pieces_per_game": 1.14, "pieces_last20": 0.7,
        "focus": {"pattern": "left a piece hanging", "habit": "Before every move, ask: what can they take?"},
        "last_game": {"opponent": "Coach-Nadia", "url": "https://www.chess.com/game/live/150000000001", "moments": 3}}


def test_two_coaches_maya_and_viktor_each_with_their_own_voice():
    """13 Oct 2026, the player's choice: Maya (af_heart, the guide's voice) and Viktor; Zara and Arjun removed."""
    assert {c: info["voice"] for c, info in coaches.COACHES.items()} == {"maya": "af_heart", "viktor": "am_michael"}
    assert all(v in voice.COACH_VOICES for v in ("af_heart", "am_michael"))


def test_each_section_always_gets_the_same_coach():
    for section in ("home", "puzzles", "review", "progress"):
        who = {coaches.speak(section, HOME, rng=random.Random(i))["coach"] for i in range(5)}
        assert len(who) == 1
    assert coaches.speak("review", HOME, moments=3)["coach"] == "maya"
    assert coaches.speak("puzzles", HOME)["coach"] == "maya" and coaches.speak("home", HOME)["coach"] == "maya"
    assert coaches.speak("progress", HOME)["coach"] == "viktor" and coaches.speak("plan", HOME)["coach"] == "viktor"


def test_greeting_names_the_player_their_focus_and_the_progress():
    said = coaches.speak("home", HOME, hour=19, rng=random.Random(1))
    text = " ".join(said["lines"])
    assert said["mood"] == "pleased" and "gushynanda" in text and "0.7" in text and "every piece safe" in text
    assert [a.get("url") or a["app"] for a in said["actions"]] == [coaches.PUZZLES, HOME["last_game"]["url"], "home"]
    assert said["actions"][0]["best"] and said["lines"][-1].startswith("My pick: Warm up with puzzles.")


def test_the_coach_recommends_where_to_practise_and_says_why():
    """13 Oct test: no preference from the coach about where to practise what, and no way back to the app."""
    def pick(section, home, now=None):
        actions, why = coaches.recommend(section, home, now=now)
        assert any(a.get("app") for a in actions), "always a way into Knightwise"
        return actions[0], why
    not_done = {**HOME, "daily": {"done_today": False}}
    best, why = pick("home", not_done)  # chess.com's home, before you play: a warm-up right there
    assert best["warmup"] and best["best"] and "your own games" in why
    best, why = coaches.recommend("home", not_done, in_app=True)  # in the app: Today's 5 minutes
    assert best[0]["app"] == "daily" and "your own games" in why
    fresh = {**HOME, "daily": {"done_today": True}, "last_game": {**HOME["last_game"], "end_time": 1000}}
    assert pick("home", fresh, now=1000 + 3600)[0]["url"] == HOME["last_game"]["url"]  # today's game: review it now
    assert pick("home", fresh, now=1000 + 3 * 86400)[0]["warmup"]  # an old one: a warm-up instead
    best, why = pick("puzzles", {**HOME, "daily": {"done_today": True}})
    assert best["app"] == "practice" and "other people's games" in why
    assert pick("progress", HOME)[0]["app"] == "progress" and pick("lessons", HOME)[0]["app"] == "plan"


def test_slipping_makes_the_coach_worried():
    said = coaches.speak("home", {**HOME, "pieces_last20": 1.6}, rng=random.Random(2))
    assert said["mood"] == "worried" and "1.6" in " ".join(said["lines"])


def test_review_of_an_unknown_game_says_nothing_about_the_board():
    said = coaches.speak("review", HOME, moments=None)
    assert said["mood"] == "thinking" and "haven't checked" in said["lines"][0] and not said["actions"]


def test_no_player_yet_points_to_the_app():
    said = coaches.speak("home", {"player": None})
    assert "Knightwise app" in said["lines"][0]


def test_every_sentence_fills_in():
    facts = dict(name="x", greet="Hi", lately=1, before=2, games=3, habit="h", tip="t", moments="2 key moments",
                 this_games=1, this_pieces=1, last_games=1, last_pieces=1)
    for kind, by_coach in coaches.SAY.items():
        for options in by_coach.values():
            for s in options:
                assert "{" not in s.format(**facts), (kind, s)


def test_chat_replies_in_character_with_the_ai():
    seen = {}
    def fake_ai(system, prompt, max_tokens):
        seen.update(system=system, prompt=prompt)
        return "Keep every piece safe before you attack!", "groq"
    r = coaches.chat("viktor", "what should I work on?", home=HOME, ask_ai=fake_ai)
    assert r["ai"] and "Viktor" in seen["system"] and "gushynanda" in seen["prompt"] and r["text"].startswith("Keep")


def test_chat_never_fails_when_the_ai_is_busy_or_missing():
    def busy(*a):
        raise RuntimeError("gemini: HTTP 503; groq: HTTP 429")
    r = coaches.chat("maya", "hello?", home=HOME, ask_ai=busy, rng=random.Random(0))
    assert not r["ai"] and "what can they take" in r["text"]


def test_chat_drops_an_ai_answer_that_invents_a_square():
    invented = lambda *a: ("Your rook on h7 was the problem.", "gemini")
    r = coaches.chat("viktor", "why did I lose?", home=HOME, ask_ai=invented)
    assert not r["ai"] and "h7" not in r["text"]


def test_progress_coach_remembers_this_week_against_last_week():
    home = {**HOME, "week": {"this": {"games": 5, "pieces": 2}, "last": {"games": 4, "pieces": 6}}}
    text = " ".join(coaches.speak("progress", home, rng=random.Random(0))["lines"])
    assert "5 games, 2 pieces" in text and "6 in 4" in text and "improvement" in text
    quiet = {**HOME, "week": {"this": {"games": 0, "pieces": 0}, "last": {"games": 3, "pieces": 1}}}
    assert "No games this week" in " ".join(coaches.speak("progress", quiet)["lines"])


def test_a_daily_or_bot_game_link_goes_to_the_archive_instead():
    home = {**HOME, "last_game": {**HOME["last_game"], "url": "https://www.chess.com/game/daily/162529818"}}
    urls = [a["url"] for a in coaches.suggestions(home)]
    assert urls[1] == "https://www.chess.com/games/archive/gushynanda"


def test_second_visit_today_is_short_not_a_new_welcome():
    """13 Oct test: the full welcome every time, or silence. The first visit of the day gets the welcome; later
    visits a short 'back again' and where things stand, never the hello again."""
    first = coaches.speak("home", HOME, hour=19, rng=random.Random(1))
    again = coaches.speak("home", HOME, hour=19, rng=random.Random(1), again=True)
    assert "gushynanda" in first["lines"][0] and "gushynanda" not in again["lines"][0]
    assert again["again"] and len(again["lines"]) == 2 and again["lines"][1].startswith("My pick")
    assert again["actions"] == first["actions"]


def test_a_profile_page_offers_prep_against_that_player_and_never_your_own():
    said = coaches.speak("member", HOME, extra={"who": "someone"})
    assert said["actions"][0]["app"] == "prep/someone" and "never during" in said["lines"][0]
    assert coaches.speak("member", HOME, extra={"who": HOME["player"]})["lines"] == []


def test_inside_the_app_no_way_back_into_the_app():
    """Full test, 14 Oct: Maya's box in Knightwise offered "Open Knightwise" and "Learn it in Knightwise"."""
    from coach import coaches
    said = coaches._for_app({"lines": ["Hi.", "My pick: Your plan in Knightwise. Because."],
                             "actions": [{"label": "Learn it in Knightwise", "app": "plan"}, coaches.OPEN_APP]})
    assert [a["label"] for a in said["actions"]] == ["Learn it"]
    assert said["lines"][1] == "My pick: Your plan. Because."
