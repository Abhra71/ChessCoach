"""Chess words, learned one at a time (owner, 28 Nov): a coach introduces a word, with a reason from the player's newest
game or now and then just because; once met, a word is ordinary text."""
import datetime
import time

from coach import nudge, words
from tests.test_nudge import HOME, fresh

DAY = datetime.date(2026, 12, 2)
ME = "me"
# White to move plays h3; Black answers Nc2+, attacking the king on e1 and the rook on a1 at once
FORK = {"fen": "4k3/8/8/8/1n6/8/7P/R3K3 w - - 0 1", "move": "h3", "reply_pv": ["b4c2"], "pattern": "other"}
QUIET_REPLY = {**FORK, "reply_pv": ["b4d5"]}


def setup(tmp_path, monkeypatch, rows):
    from coach import insights
    monkeypatch.setattr(words, "FILE", tmp_path / "words.json")
    g = {"url": "https://www.chess.com/game/live/77", "end_time": time.time() - 3600,
         "white": {"username": ME, "result": "resigned"}, "black": {"username": "Rival", "result": "win"}, "pgn": ""}
    monkeypatch.setattr(insights, "_moves", lambda: {g["url"]: rows})
    home = {**HOME, "daily": {"done_today": True},
            "last_game": {"id": "77", "opponent": "Rival", "end_time": g["end_time"], "result": "loss"}}
    return home, [g]


def test_a_fork_is_seen_in_their_reply():
    assert words.forked(FORK) and not words.forked(QUIET_REPLY) and not words.forked({})


def test_the_game_gives_the_reason(tmp_path, monkeypatch):
    home, games = setup(tmp_path, monkeypatch, [FORK, {**QUIET_REPLY, "pattern": "left a piece hanging"}])
    got = words.introductions(home, games, ME, DAY)
    assert [w for w, _, _ in got] == ["Fork", "Blunder, mistake, inaccuracy", "Hanging piece"]
    word, coach, line = got[0]
    assert coach == "maya" and line.startswith("Against Rival, one of their pieces attacked two of yours")
    assert "fork" in line.lower()  # the word itself is in the line, so the app marks it the first time


def test_once_met_never_introduced_again(tmp_path, monkeypatch):
    home, games = setup(tmp_path, monkeypatch, [FORK])
    words.met("Fork")
    got = [w for w, _, _ in words.introductions(home, games, ME, DAY)]
    assert "Fork" not in got


def test_without_a_reason_one_word_a_week(tmp_path, monkeypatch):
    home, games = setup(tmp_path, monkeypatch, [])
    first = words.introductions(home, games, ME, DAY)
    assert first == [("Candidate moves", "maya", "A chess word for you: candidate moves. The 2–3 moves worth "
                      "thinking about before you choose.")]  # Notation has no form to mark, so the list starts here
    words.introduced("Candidate moves", DAY)
    assert words.introductions(home, games, ME, DAY + datetime.timedelta(days=3)) == []
    nxt = words.introductions(home, games, ME, DAY + datetime.timedelta(days=7))
    assert nxt[0][0] == "Hanging piece"


def test_a_coach_introduces_it_first_in_their_own_voice(tmp_path, monkeypatch):
    fresh(tmp_path, monkeypatch, club=True)
    from coach import memories
    home, games = setup(tmp_path, monkeypatch, [FORK])
    for told in ("welcome", "hundred"):
        memories.told(told)
    p = nudge.pick("app", "home", home, DAY, games=games, player=ME)
    assert p["kind"] == "word" and p["id"] == "word-Fork" and p["voice"] == "maya"
    assert "Fork" in words._load()["introduced"]
    later = nudge.candidates("app", home, games=games, player=ME, day=DAY + datetime.timedelta(days=1))
    assert not [c for c in later if c["id"] == "word-Fork"]


def test_the_app_learns_which_words_were_met(tmp_path, monkeypatch):
    monkeypatch.setattr(words, "FILE", tmp_path / "words.json")
    assert words.page()["met"] == [] and words.page()["per_page"] == 2
    assert words.met("Pin") and not words.met("nonsense")
    assert words.page()["met"] == ["Pin"]


def test_words_met_at_the_same_moment_are_all_kept(tmp_path, monkeypatch):
    """28 Nov UI check: two words met at once, and one save overwrote the other."""
    import threading
    monkeypatch.setattr(words, "FILE", tmp_path / "words.json")
    names = [w for w, _, _ in words.WORDS][:12]
    ts = [threading.Thread(target=words.met, args=(w,)) for w in names] + \
         [threading.Thread(target=words.looked_up, args=(w,)) for w in names]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(words.page()["met"]) == sorted(names) and len(words.page()["looked"]) == 12
