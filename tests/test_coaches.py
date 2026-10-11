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
    facts = dict(name="x", greet="Hi", lately=1, before=2, games=3, habit="h", tip="t", moments="2 key moments")
    for kind, by_coach in coaches.SAY.items():
        for options in by_coach.values():
            for s in options:
                assert "{" not in s.format(**facts), (kind, s)
