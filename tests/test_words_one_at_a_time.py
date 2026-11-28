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


def test_without_a_reason_one_word_every_few_days(tmp_path, monkeypatch):
    home, games = setup(tmp_path, monkeypatch, [])
    first = words.introductions(home, games, ME, DAY)
    assert first == [("Candidate moves", "maya", "A chess word for you: candidate moves. The 2–3 moves worth "
                      "thinking about before you choose.")]  # Notation has no form to mark, so the list starts here
    words.introduced("Candidate moves", DAY)
    assert words.introductions(home, games, ME, DAY + datetime.timedelta(days=2)) == []
    nxt = words.introductions(home, games, ME, DAY + datetime.timedelta(days=3))
    assert nxt[0][0] == "Hanging piece"


def test_the_coach_says_the_word_first_without_waiting_for_a_suggestion_slot(tmp_path, monkeypatch):
    """Owner, 29 Nov ("where are the words?"): the day's three suggestions were all taken by the new game, the
    5 minutes and the rematch, so no word was ever introduced. Now the word is the coach's first line, once a day."""
    from coach import insights, service
    home, games = setup(tmp_path, monkeypatch, [FORK])
    monkeypatch.setattr(insights, "home", lambda: home)
    monkeypatch.setattr(insights, "_games", lambda: games)
    monkeypatch.setattr(insights, "_player", lambda: ME)
    q = {"in": "app", "section": "home", "tab": "home"}
    busy = {"coach": "viktor", "lines": ["Good evening.", "New game in, against Rival."], "actions": [],
            "point": {"kind": "game", "line": "New game in, against Rival."}}
    said = service.with_word(busy, q)
    assert said["coach"] == "maya" and said["word"] == "Fork"
    assert said["lines"][0].startswith("Against Rival, one of their pieces attacked two of yours")
    assert said["lines"][1] == "New game in, against Rival."  # the day's suggestion is still there
    assert service.with_word(busy, q) is busy  # one word a day
    quiet = {"coach": "maya", "lines": [], "quiet": True}
    assert service.with_word(quiet, {**q, "tab": "train"}) is quiet  # already one today
    assert service.with_word(busy, {**q, "tab": "practice"}) is busy  # never where you're working
    story = {**busy, "point": {"kind": "memory", "voice": "viktor", "line": "x"}}
    words.FILE.write_text("{}")
    assert service.with_word(story, q) is story  # a coach's own story is being told: the word waits


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
