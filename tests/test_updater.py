"""1.2: the quiet update. Only when a newer version is out, only at a calm moment, once a day per version, and never
quitting without a comeback scheduled."""
import json
import threading
import time

import pytest

from coach import fixes, updater


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A Store copy of Knightwise 1.2.0, its own data folder, a calm PC (window away and no use for an hour)."""
    monkeypatch.setattr(updater, "PACKAGED", True)
    monkeypatch.setattr(updater, "VERSION", "1.2.0")
    monkeypatch.setattr(updater, "FILE", tmp_path / "update-try.json")
    monkeypatch.setattr(fixes, "FILE", tmp_path / "fixes.json")
    monkeypatch.setattr(updater, "WINDOW", {"shown": False, "since": time.time() - 3600})
    monkeypatch.setattr(updater, "USE", {"at": time.time() - 3600})
    return tmp_path


def say_latest(tmp_path, v):
    (tmp_path / "fixes.json").write_text(json.dumps({"at": time.time(), "fixes": fixes.clean({"latest": v})}))


READY = {"phase": "ready"}


def test_versions_compare_as_numbers():
    assert updater.newer("1.10.0", "1.9.0") and updater.newer("1.2.1", "1.2.0") and updater.newer("2.0", "1.9.9")
    assert not updater.newer("1.2.0", "1.2.0") and not updater.newer("1.1.0", "1.2.0")
    assert not updater.newer(None, "1.2.0") and not updater.newer("", "1.2.0")


def test_the_fix_file_keeps_only_a_real_version_number():
    assert fixes.clean({"latest": "1.3.0"})["latest"] == "1.3.0"
    for bad in ("1.3.0; rm -rf", "latest", 13, ["1.3"], "1", "1.2.3.4.5"):
        assert fixes.clean({"latest": bad})["latest"] is None


def test_nothing_happens_when_we_are_current(store):
    say_latest(store, "1.2.0")
    assert not updater.should_try(READY, busy=False) and updater.status() is None


def test_a_newer_version_at_a_calm_moment_tries_once_a_day(store, monkeypatch):
    say_latest(store, "1.3.0")
    assert updater.should_try(READY, busy=False)
    assert updater.status() == {"latest": "1.3.0", "tried": False}
    quits = []
    monkeypatch.setattr(updater, "_schedule", lambda route, minutes=2: True)  # no real scheduled task in a test
    assert updater.restart(lambda: quits.append(1))
    assert quits == [1]
    assert not updater.should_try(READY, busy=False)  # tried today already
    assert updater.status() == {"latest": "1.3.0", "tried": True}  # Home now offers the Store too
    assert updater.should_try(READY, busy=False, today="2099-01-01")  # tomorrow: once more


def test_never_while_the_player_is_here_or_a_check_runs(store):
    say_latest(store, "1.3.0")
    assert not updater.should_try(READY, busy=True)  # the game check holds the lock
    assert not updater.should_try({"phase": "checking your games"}, busy=False)
    assert not updater.should_try({"phase": "ready", "older": {"done": 3, "total": 90}}, busy=False)
    updater.used("/api/home")  # the player opened a page a moment ago
    assert not updater.should_try(READY, busy=False)


def test_timers_are_not_the_player(store):
    say_latest(store, "1.3.0")
    for timer in ("/api/status", "/api/extension-stamp", "/api/hello", "/api/fixes?x=1"):
        updater.used(timer)
    assert updater.should_try(READY, busy=False)


def test_the_window_open_or_just_closed_is_not_calm(store):
    say_latest(store, "1.3.0")
    updater.window(True)
    assert not updater.should_try(READY, busy=False)
    updater.window(False)  # closed just now: wait the 10 minutes
    assert not updater.should_try(READY, busy=False)
    assert updater.should_try(READY, busy=False, now=time.time() + 11 * 60)


def test_no_quit_without_a_comeback(store, monkeypatch):
    say_latest(store, "1.3.0")
    monkeypatch.setattr(updater, "_schedule", lambda route, minutes=2: False)
    quits = []
    assert not updater.restart(lambda: quits.append(1))
    assert quits == [] and not (store / "update-try.json").exists()


def test_from_source_never(store, monkeypatch):
    monkeypatch.setattr(updater, "PACKAGED", False)
    say_latest(store, "9.0.0")
    assert not updater.should_try(READY, busy=False) and updater.status() is None


def test_after_the_restart_the_logbook_says_whether_it_took(store, monkeypatch, caplog):
    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: None)  # the task removal
    (store / "update-try.json").write_text(json.dumps({"version": "1.3.0", "day": "2026-11-26", "from": "1.2.0"}))
    with caplog.at_level("INFO", logger="knightwise"):
        updater.on_start()
    assert "isn't downloaded yet" in caplog.text and (store / "update-try.json").exists()
    monkeypatch.setattr(updater, "VERSION", "1.3.0")
    with caplog.at_level("INFO", logger="knightwise"):
        updater.on_start()
    assert "now 1.3.0 (was 1.2.0)" in caplog.text and not (store / "update-try.json").exists()


def test_the_watch_restarts_by_itself(store, monkeypatch):
    say_latest(store, "1.3.0")
    monkeypatch.setattr(updater, "EVERY", 0.01)
    monkeypatch.setattr(updater, "_schedule", lambda route, minutes=2: True)
    quit = threading.Event()
    updater.watch(dict(READY), threading.Lock(), quit.set)
    assert quit.wait(3)


def test_the_quiet_comeback_never_pops_up_a_running_window(monkeypatch):
    """Bug hunt 27 Nov: chesscoach://background finding Knightwise already running used to ask it to show Home."""
    from coach import app
    shown = []
    monkeypatch.setattr(app, "ask_running_copy", lambda route: shown.append(route) or True)
    app.hand_over("home", background=True)
    assert shown == []
    app.hand_over("practice", background=False)  # the player's own start still brings it forward
    assert shown == ["practice"]
