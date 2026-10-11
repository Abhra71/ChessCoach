import random

from coach import coaches, voice

HOME = {"player": "gushynanda", "games": 140, "pieces_per_game": 1.14, "pieces_last20": 0.7,
        "focus": {"pattern": "left a piece hanging", "habit": "Before every move, ask: what can they take?"},
        "last_game": {"opponent": "Coach-Nadia", "url": "https://www.chess.com/game/daily/162529818", "moments": 3}}


def test_two_women_two_men_each_with_their_own_voice():
    voices = [c["voice"] for c in coaches.COACHES.values()]
    assert len(coaches.COACHES) == 4 and len(set(voices)) == 4
    assert sorted(v[1] for v in voices) == ["f", "f", "m", "m"]  # Kokoro names: af_/bf_ = woman, am_/bm_ = man
    assert all(v in voice.COACH_VOICES for v in voices)


def test_each_section_always_gets_the_same_coach():
    for section in ("home", "puzzles", "review", "progress"):
        who = {coaches.speak(section, HOME, rng=random.Random(i))["coach"] for i in range(5)}
        assert len(who) == 1
    assert coaches.speak("review", HOME, moments=3)["coach"] == "maya"
    assert coaches.speak("puzzles", HOME)["coach"] == "arjun"


def test_greeting_names_the_player_their_focus_and_the_progress():
    said = coaches.speak("home", HOME, hour=19, rng=random.Random(1))
    text = " ".join(said["lines"])
    assert said["mood"] == "pleased" and "gushynanda" in text and "0.7" in text and "every piece safe" in text
    assert [a["url"] for a in said["actions"]] == [coaches.PUZZLES, HOME["last_game"]["url"]]


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
    r = coaches.chat("arjun", "what should I work on?", home=HOME, ask_ai=fake_ai)
    assert r["ai"] and "Arjun" in seen["system"] and "gushynanda" in seen["prompt"] and r["text"].startswith("Keep")


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
