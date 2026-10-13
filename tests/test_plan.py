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
    assert new["id"] == "tactic:fork" and new["coach"] == "viktor" and "new for you" in new["why"]


def test_ai_idea_is_written_for_the_player_and_checked(memory):
    ok = lambda *a: ('{"title": "Look before you leap", "text": "Pause on every capture. Ask what changed."}', "groq")
    idea = plan.ai_idea(HOME, today=date(2026, 10, 5), ask_ai=ok)
    assert idea["title"] == "Look before you leap" and idea["ai"]
    again = plan.ai_idea(HOME, today=date(2026, 10, 6), ask_ai=lambda *a: 1 / 0)  # same week: from memory, no AI call
    assert again["id"] == idea["id"] and again["checklist"]


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


def test_an_idea_is_practised_on_the_board_with_its_checklist(memory):
    lesson = plan.idea_lesson(plan.IDEAS[0], 400, random.Random(0))
    assert lesson["checklist"][0] == "After my move, what can they take?" and lesson["drills"]


def test_daily_streak_forgives_one_missed_day_but_not_two():
    from coach import daily
    today = date(2026, 10, 10)
    assert daily.streak(["2026-10-10", "2026-10-09", "2026-10-07"], today) == 3  # the 8th was missed: forgiven
    assert daily.streak(["2026-10-10", "2026-10-06"], today) == 1  # two missed days: a new run
    assert daily.streak(["2026-10-08"], today) == 1 and daily.streak(["2026-10-07"], today) == 0
    assert daily.week_dots(["2026-10-10", "2026-10-04"], today) == [True, False, False, False, False, False, True]


def test_badges_count_runs_of_real_games_without_the_habit():
    from coach import progress
    games = [{"url": f"g{i}"} for i in range(8)]  # newest first
    moves = {f"g{i}": [] for i in range(8)}
    moves["g2"] = [{"pattern": progress.HANG}]
    assert progress.runs(games, moves, progress.HANG) == (2, 5)  # 2 since the last one, best run 5
    clean = {g["url"]: [] for g in games}  # 8 clean games in a row
    safe = next(b for b in progress.badges(games, clean) if b["id"] == "safe")
    assert safe["tier_name"] == "Silver" and safe["next"] == 10


def test_opening_tree_counts_results_per_branch_and_names_them():
    from coach import tree
    pgn = lambda moves: f'[Event "x"]\n\n{moves} *'
    games = [{"white": {"username": "me", "result": r}, "black": {"username": "x", "result": "win" if r != "win" else "checkmated"},
              "pgn": pgn(m)} for m, r in [("1. e4 e5 2. Nf3", "win"), ("1. e4 e5 2. Nf3", "checkmated"), ("1. d4 d5", "win")]]
    t = tree.build(games, "me")["white"]
    e4 = t["children"][0]
    assert (e4["san"], e4["games"], e4["score"], e4["name"]) == ("e4", 2, 50, "King's Pawn Game")
    assert e4["children"][0]["children"][0]["name"] == "King's Knight Opening"
