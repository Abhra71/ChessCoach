import pytest


@pytest.fixture(scope="session", autouse=True)
def close_the_shared_engine():
    """Tests that play moves open the app's shared Stockfish (coach/live_engine.py): close it at the end, or the
    test run never finishes."""
    yield
    from coach import live_engine
    if live_engine._engine is not None:
        live_engine._engine.quit()
        live_engine._engine = None
