"""A new install starts from the packed puzzles instead of a 300 MB download (22 Oct test, finding 1)."""
import json

from coach import puzzles


def test_pack_is_used_when_current(tmp_path, monkeypatch):
    pack, out = tmp_path / "pack.json", tmp_path / "data" / "puzzles.json"
    pack.write_text(json.dumps({"fork": [], "_version": puzzles.VERSION}))
    monkeypatch.setattr(puzzles, "PACK", pack)
    monkeypatch.setattr(puzzles, "OUT", out)
    assert puzzles.from_pack() and puzzles.current()


def test_old_pack_is_not_used(tmp_path, monkeypatch):
    pack = tmp_path / "pack.json"
    pack.write_text(json.dumps({"_version": puzzles.VERSION - 1}))
    monkeypatch.setattr(puzzles, "PACK", pack)
    monkeypatch.setattr(puzzles, "OUT", tmp_path / "out.json")
    assert not puzzles.from_pack()
