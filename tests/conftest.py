import pytest


@pytest.fixture(autouse=True)
def drills_cache_of_its_own(tmp_path, monkeypatch):
    """Each test keeps its drills' engine work in its own folder, never in data/ (19 Oct)."""
    from coach import drills
    monkeypatch.setattr(drills, "CACHE", tmp_path / "drill-cache.json")
    monkeypatch.setattr(drills, "_cache", None)
    from coach import heard
    monkeypatch.setattr(heard, "FILE", tmp_path / "heard.jsonl")
    monkeypatch.setattr(heard, "WORDS", tmp_path / "heard-words.json")


@pytest.fixture(scope="session", autouse=True)
def close_the_shared_engine():
    """Tests that play moves open the app's shared Stockfish (coach/live_engine.py): close it at the end, or the
    test run never finishes."""
    yield
    from coach import live_engine
    if live_engine._engine is not None:
        live_engine._engine.quit()
        live_engine._engine = None
