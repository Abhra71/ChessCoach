import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_engine: the test plays real Stockfish moves")


def pytest_collection_modifyitems(config, items):
    """Without Stockfish (a fresh copy of the repo: engine/ isn't in git), the tests that need it are skipped with a
    reason instead of failing (27 Nov: 6 tests failed with FileNotFoundError in a new worktree)."""
    from coach.paths import ENGINE
    if ENGINE.exists():
        return
    skip = pytest.mark.skip(reason=f"Stockfish isn't at {ENGINE} (python -m coach.get_engine, or set KNIGHTWISE_ENGINE)")
    for item in items:
        if "needs_engine" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def drills_cache_of_its_own(tmp_path, monkeypatch):
    """Each test keeps its drills' engine work in its own folder, never in data/ (19 Oct)."""
    from coach import drills
    monkeypatch.setattr(drills, "CACHE", tmp_path / "drill-cache.json")
    monkeypatch.setattr(drills, "_cache", None)
    from coach import heard
    monkeypatch.setattr(heard, "FILE", tmp_path / "heard.jsonl")
    monkeypatch.setattr(heard, "WORDS", tmp_path / "heard-words.json")
    from coach import coaches
    monkeypatch.setattr(coaches, "SAID", tmp_path / "said.json")


@pytest.fixture(scope="session", autouse=True)
def close_the_shared_engine():
    """Tests that play moves open the app's shared Stockfish (coach/live_engine.py): close it at the end, or the
    test run never finishes."""
    yield
    from coach import live_engine
    if live_engine._engine is not None:
        live_engine._engine.quit()
        live_engine._engine = None
