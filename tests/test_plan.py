import random
from datetime import date

import chess
import pytest

from coach import openings, plan


def test_every_opening_in_the_catalogue_is_legal_chess():
    lines = openings.catalogue()
    assert len(lines) > 3000
    for eco, name, sans in lines:
        board = chess.Board()
        for san in sans:
            board.push_san(san)  # raises if a move is illegal


def test_opening_drill_plays_your_side_and_explains_each_move():
    lesson = {"id": "opening:B12:Caro-Kann Defense: Main Line", "name": "Caro-Kann Defense: Main Line", "side": "black",
              **openings.teach(["e4", "c6", "d4", "d5", "Nc3", "dxe4", "Nxe4"], "black")}
    d = plan.opening_drill(lesson)
    assert d["flip"] and d["last"] == ["e2", "e4"]
    firsts = [next(m["san"] for m in st["moves"].values() if m["good"]) for st in d["steps"]]
    assert firsts == ["c6", "d5", "dxe4"]
    assert all(st["idea"] for st in d["steps"]) and "Not in this opening" in d["steps"][0]["moves"]["e7e5"]["say"]


def game(url, end, result="loss", white="me"):
    return {"url": url, "end_time": end, "white": {"username": white, "result": result},
            "black": {"username": "them", "result": "win" if result == "loss" else "loss"}}


@pytest.fixture
def memory(tmp_path, monkeypatch):
    monkeypatch.setattr(plan, "MEMORY", tmp_path / "novelty.json")
    monkeypatch.setattr(plan, "_puzzles", lambda theme, rating, rng, avoid=(): [{"id": theme}])


HOME = {"player": "me", "games": 30, "rating": 400, "pieces_per_game": 1.0, "pieces_last20": 0.5,
        "focus": {"pattern": plan.HANG}}


def test_a_stalemated_win_brings_the_endgame_lesson_once_then_it_stays_until_done(memory):
    games = [game(f"g{i}", 1000 - i) for i in range(30)]
    moves = {g["url"]: [] for g in games}
    moves["g3"] = [{"pattern": plan.STALEMATE, "ply": 80}]
    first = plan.novelty(HOME, games, moves, today=date(2026, 10, 1))
    assert first["id"] == "endgame:queenEndgame" and "stalemated 1 won game." in first["why"]
    plan.mark(first["id"], today=date(2026, 10, 1), novelty=True)
    again = plan.novelty(HOME, games, moves, today=date(2026, 10, 2))
    assert again["id"] == first["id"] and again["again"] and again["why"] == first["why"]
    plan.mark(first["id"], done=True)
    assert plan.novelty(HOME, games, moves, today=date(2026, 10, 2)) is None  # cooldown: nothing new for a few days


def test_nothing_new_when_nothing_is_needed(memory):
    games = [game(f"g{i}", 1000 - i, result="win") for i in range(30)]
    moves = {g["url"]: [] for g in games}
    assert plan.novelty(HOME, games, moves, today=date(2026, 10, 1)) is None


def test_a_new_kind_of_mistake_brings_a_tactic_for_it(memory):
    games = [game(f"g{i}", 1000 - i, result="win") for i in range(30)]
    moves = {g["url"]: [] for g in games}
    for g in games[:5]:  # forks only in the last games
        moves[g["url"]] = [{"pattern": plan.FORK, "ply": 40}]
    new = plan.novelty(HOME, games, moves, today=date(2026, 10, 1), rng=random.Random(1))
    assert new["id"] == "tactic:fork" and new["coach"] == "arjun" and "new for you" in new["why"]


def test_ai_idea_is_written_for_the_player_and_checked(memory):
    ok = lambda *a: ('{"title": "Look before you leap", "text": "Pause on every capture. Ask what changed."}', "groq")
    idea = plan.ai_idea(HOME, today=date(2026, 10, 5), ask_ai=ok)
    assert idea["title"] == "Look before you leap" and idea["ai"]
    again = plan.ai_idea(HOME, today=date(2026, 10, 6), ask_ai=lambda *a: 1 / 0)  # same week: from memory, no AI call
    assert again == idea


def test_ai_idea_with_a_move_in_it_is_dropped(memory):
    bad = lambda *a: ('{"title": "Play e4", "text": "Always play e4 first."}', "gemini")
    assert plan.ai_idea(HOME, today=date(2026, 10, 5), ask_ai=bad) is None
    busy = lambda *a: (_ for _ in ()).throw(RuntimeError("503"))
    assert plan.ai_idea(HOME, today=date(2026, 10, 5), ask_ai=busy) is None


def test_opening_a_plan_card_is_not_a_new_thing(memory):
    games = [game(f"g{i}", 1000 - i, result="win") for i in range(30)]
    moves = {g["url"]: [] for g in games}
    plan.mark("tactic:pin", today=date(2026, 10, 1))  # opened from Your plan
    assert plan.novelty(HOME, games, moves, today=date(2026, 10, 1)) is None
