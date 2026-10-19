"""The fix file (flagship 6): what a bad or hostile edit can and can't do, and that offline keeps the last copy."""
import json

from coach import fixes


def test_only_short_strings_and_known_features_are_kept():
    raw = {"boards": ["wc-board-2026", 7, "x" * 500], "off": ["tags", "everything", "review"],
           "nav": {"puzzles": ["a[href='/puzzles']", None]}, "evil": "<script>"}
    out = fixes.clean(raw)
    assert out["boards"] == ["wc-board-2026"] and out["off"] == ["tags", "review"]
    assert out["nav"] == {"puzzles": ["a[href='/puzzles']"]} and "evil" not in out
    assert fixes.clean("not a dict")["off"] == []


def test_downloaded_once_a_day_and_offline_keeps_the_last_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(fixes, "FILE", tmp_path / "fixes.json")
    assert fixes.refresh(fetch=lambda: {"off": ["warmup"]})["off"] == ["warmup"]
    assert fixes.refresh(fetch=lambda: {"off": []})["off"] == ["warmup"]  # within the day: not fetched again

    def offline():
        raise OSError("no internet")
    assert fixes.refresh(force=True, fetch=offline)["off"] == ["warmup"]


def test_the_repo_file_is_valid_and_empty():
    from pathlib import Path
    raw = json.loads((Path(__file__).resolve().parents[1] / "fixes.json").read_text())
    assert fixes.clean(raw) == fixes.clean({}) and raw["version"] == 1
