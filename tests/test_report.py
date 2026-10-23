"""The report for a coach, and Wrapped (1.0): facts from the games in the period, against the period before."""
import time

from coach import report

DAY = 86400
NOW = 1_800_000_000


def game(n, result, rating, days_ago):
    return {"url": f"https://www.chess.com/game/live/{n}", "end_time": NOW - days_ago * DAY, "time_class": "rapid",
            "pgn": "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+ 7. Nc3 Nxe4 8. O-O Bxc3 9. d5 Bf6 10. Re1 Ne7 *",
            "white": {"username": "me", "result": result, "rating": rating}, "black": {"username": f"o{n}", "result": "x", "rating": 400}}


def test_a_week_against_the_week_before(monkeypatch):
    games = [game(1, "win", 420, 1), game(2, "resigned", 410, 3), game(3, "win", 400, 9), game(4, "win", 390, 10)]
    hang = {"pattern": "left a piece hanging", "loss": 40, "ply": 15, "move": "Qe5", "best": "Qd5", "cp_before": 0,
            "cp_after": -300, "color": "white", "stalemate": False, "best_mates": False, "allows_mate": False,
            "best_is_capture": False, "mat_before": 39, "fen": "4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", "reply_pv": ["d6e5"]}
    moves = {g["url"]: ([hang, hang] if g["end_time"] < NOW - 7 * DAY else [hang]) for g in games}
    monkeypatch.setattr(report.insights, "_player", lambda: "me")
    monkeypatch.setattr(report.insights, "_games", lambda: games)
    monkeypatch.setattr(report.insights, "_moves", lambda: moves)
    monkeypatch.setattr(report.insights, "home", lambda: {"focus": {"habit": "Keep every piece safe.", "pattern": "left a piece hanging"}})
    monkeypatch.setattr(report, "_practice", lambda since, until: {"answers": 6, "right": 4, "days": 3})
    r = report.report(7, now=NOW)
    assert r["games"] == 2 and r["results"] == {"win": 1, "loss": 1} and r["rating"] == {"from": 400, "to": 420, "kind": "rapid"}
    assert r["pieces"] == {"now": 1.0, "before": 2.0}
    assert r["habits"][0]["pattern"] == "left a piece hanging" and r["habits"][0]["before"] == 2.0
    assert r["worst"]["move"] == "Qe5" and r["worst"]["best"] == "Qd5"
    assert r["lines"][0].startswith("Only 2 games") and "1 won, 0 drawn, 1 lost" in r["lines"][1] and any("fewer than the period before (2.0)" in l for l in r["lines"])
    assert any("Practised on 3 days: 6 positions, 4 right first time." == l for l in r["lines"])


def test_an_empty_week_says_so():
    r = {"games": 0, "days": 7}
    assert report.lines(r)[0].startswith("No games in these 7 days.")


def _setup(monkeypatch, games):
    hang = {"pattern": "left a piece hanging", "loss": 40, "ply": 15, "move": "Qe5", "best": "Qd5", "cp_before": 0,
            "cp_after": -300, "color": "white", "stalemate": False, "best_mates": False, "allows_mate": False,
            "best_is_capture": False, "mat_before": 39, "fen": "4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", "reply_pv": ["d6e5"]}
    monkeypatch.setattr(report.insights, "_player", lambda: "me")
    monkeypatch.setattr(report.insights, "_games", lambda: games)
    monkeypatch.setattr(report.insights, "_moves", lambda: {g["url"]: [hang] for g in games})
    monkeypatch.setattr(report.insights, "home", lambda: {"focus": {}})
    monkeypatch.setattr(report, "_practice", lambda since, until: {"answers": 0, "right": 0, "days": 0})


def test_ratings_are_per_kind_of_game_and_a_loss_is_never_the_best_game(monkeypatch):
    blitz_old = {**game(5, "win", 155, 150), "time_class": "blitz"}
    blitz = {**game(6, "timeout", 100, 1), "time_class": "blitz"}
    games = [game(1, "resigned", 293, 2), game(2, "win", 311, 9), blitz, blitz_old]
    _setup(monkeypatch, games)
    r = report.report(7, now=NOW)
    assert {(x["kind"], x["from"], x["to"]) for x in r["ratings"]} == {("rapid", 311, 293), ("blitz", 155, 100)}
    assert "best" not in r  # two losses: no "best game"
    assert any(l.startswith("Rating: ") and "blitz 155 to 100 (-55)" in l and "rapid 311 to 293 (-18)" in l for l in r["lines"])
