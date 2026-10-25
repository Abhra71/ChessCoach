"""The coach reaches every part of the app from the player's own mistakes (25 Oct): 3 suggestions a day in all, the
tour included; one from their mistakes before the tour; each says why and exactly where; and the end of a game review
links that game's mistake to its training."""
import datetime
import time

from coach import bridge, nudge

DAY = datetime.date(2026, 10, 26)
HOME = {"games": 140, "daily": {"done_today": True}, "focus": {"pattern": "left a piece hanging"}, "last_game": {}}
TOUR = [("blindfold", "viktor", "blindfold", "blindfold", None, "Try Blindfold."),
        ("guess", "viktor", "guess", "guess", None, "Try Guess the move."),
        ("endgames", "viktor", "endgames", "endgames", None, "Try Endgames."),
        ("calc", "viktor", "calc", "calc", None, "Try In your head.")]
LESSON = {"id": "safe-hanging", "title": "Keep every piece safe", "habit": "Is it safe?",
          "why": "In your last 20 games: 0.45 a game (pieces left hanging). The goal is 0.3."}


def fresh(tmp_path, monkeypatch):
    from coach import plan
    monkeypatch.setattr(nudge, "FILE", tmp_path / "nudges.json")
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    monkeypatch.setattr(nudge, "TOUR", TOUR)
    monkeypatch.setattr(nudge, "GAP", 0)
    monkeypatch.setattr(nudge, "TOUR_GAP", 0)


def test_three_a_day_in_all_with_their_own_mistake_before_the_tour(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    got = [nudge.pick("app", "home", HOME, DAY, lesson=LESSON) for _ in range(5)]
    kinds = [p["kind"] if p else None for p in got]
    assert kinds[0] == "lesson"  # their mistake first
    assert kinds[1:3] == ["tour", "tour"]
    assert kinds[3:] == [None, None]  # 3 in all: the tour has no 3 of its own on top


def test_the_lesson_says_why_from_their_numbers_and_exactly_where(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    p = nudge.pick("app", "home", HOME, DAY, lesson=LESSON)
    assert p["line"].startswith("In your last 20 games: 0.45 a game (pieces left hanging). Your next lesson: Keep every")
    assert p["line"].endswith("It's the card at the top of Your course, in the menu.") and p["route"] == "course/safe-hanging"


def test_a_basics_lesson_without_numbers_says_what_it_teaches(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    p = nudge.pick("app", "home", HOME, DAY, lesson={**LESSON, "why": ""})
    assert p["line"].startswith("It teaches: Is it safe? Your next lesson: Keep every piece safe.")  # no "?."


def _game(i, url, cp=0, pattern=None):
    return {"url": url, "end_time": time.time() - i * 3600, "white": {"username": "me", "result": "loss"},
            "black": {"username": "them", "result": "win"}}


def test_stalemated_won_games_point_to_the_exact_ending(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch)
    from coach import insights
    games = [_game(i, f"u{i}") for i in range(4)]
    moves = {"u0": [{"pattern": "stalemated a won game", "cp_before": 900, "loss": 90, "ply": 80}]}
    monkeypatch.setattr(insights, "_moves", lambda: moves)
    monkeypatch.setattr(insights, "_player", lambda: "me")
    got = nudge.candidates("app", HOME, None, None, None, games, "me")
    end = next(c for c in got if c["kind"] == "endgame")
    assert end["route"] == "endgame/queen" and end["line"].startswith("You stalemated 1 won game in your last 20.")
    assert end["line"].endswith("In Train, open Endgames.")


def test_the_end_of_a_review_links_this_games_mistake_to_its_training(tmp_path, monkeypatch):
    games = [_game(i, f"https://www.chess.com/game/live/{i}") for i in range(5)]
    hang = {"pattern": "left a piece hanging", "cp_before": 0, "loss": 30, "ply": 20}
    moves = {g["url"]: [hang] for g in games}
    moves[games[0]["url"]] = [hang, hang]
    monkeypatch.setattr(bridge, "_own_positions", lambda p: 4)
    b = bridge.for_game("0", games, moves)
    assert b == {"line": "You left a piece hanging twice in this game and 6 times in your last 5 games: Practice has 4 "
                         "of your own positions on it.", "route": "practice/left a piece hanging", "label": "Practise it"}
    monkeypatch.setattr(bridge, "_own_positions", lambda p: 0)  # none of their own: the lesson instead
    assert bridge.for_game("0", games, moves)["route"] == "course/safe-hanging"
    mate = {"pattern": "missed a checkmate", "cp_before": 0, "loss": 50, "ply": 30}
    assert bridge.for_game("1", games, {games[1]["url"]: [mate]})["route"] == "course/safe-mate1"
    assert bridge.for_game("2", games, {games[2]["url"]: []}) is None  # a clean game: nothing to link
