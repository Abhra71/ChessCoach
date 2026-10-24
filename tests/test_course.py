"""The course follows you: your games pick the next lesson, and only your games after it pass a lesson."""
import pytest

from coach import course


T = 1_700_000_000


def games(n, start=T):
    return [{"url": f"g{start + i}", "end_time": start + i} for i in range(n)][::-1]  # newest first, as the app keeps them


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(course, "FILE", tmp_path / "course.json")
    def make(gs, idea_per_game):
        tags = {g["url"]: [(10, idea, 30) for idea, n in idea_per_game(g).items() for _ in range(n)] for g in gs}
        monkeypatch.setattr(course, "tags", lambda moves=None: tags)
        return {g["url"]: [{}] for g in gs}
    return make


def test_the_next_lesson_is_the_mistake_that_costs_most(setup):
    gs = games(20)
    moves = setup(gs, lambda g: {"hanging": 1, "threats": 0})
    c = course.course(gs, moves, "me", current="safe")
    assert c["next"] == "basics-values"  # like an academy: the basics first, on the first level (24 Oct)
    for lid in ("basics-values", "basics-cheapest", "basics-mates"):
        course.studied(lid, 3, 3)
    c = course.course(gs, moves, "me", current="safe")
    assert c["next"] == "safe-hanging"
    rows = {r["id"]: r for r in c["lessons"]}
    assert rows["safe-hanging"]["rate"] == 1.0
    assert rows["safe-guard"]["status"] == "fine"  # never happens: "you already do this"
    assert rows["tac-fork"]["status"] == "later"  # above your level
    assert rows["exp-prophylaxis"]["status"] == "coming"  # not ready yet
    assert rows["pre-iqp"]["status"] == "later"  # ready: the strong players' library has the isolated pawn


def test_a_lesson_passes_only_when_your_games_after_it_improve(setup):
    old = games(20)
    moves = setup(old, lambda g: {"hanging": 1})
    course.studied("safe-hanging", 3, 4, today=__import__("datetime").datetime.fromtimestamp(T + 1000))
    rows = {r["id"]: r for r in course.course(old, moves, "me", current="safe")["lessons"]}
    assert rows["safe-hanging"]["status"] == "watching"  # studied, no games since
    new = games(5, start=T + 2000) + old
    moves = setup(new, lambda g: {} if g["end_time"] >= T + 2000 else {"hanging": 1})
    rows = {r["id"]: r for r in course.course(new, moves, "me", current="safe")["lessons"]}
    assert rows["safe-hanging"]["status"] == "passed"
    still = setup(new, lambda g: {"hanging": 1})
    rows = {r["id"]: r for r in course.course(new, still, "me", current="safe")["lessons"]}
    assert rows["safe-hanging"]["status"] == "again"


def test_every_idea_the_coach_names_has_a_lesson():
    from coach import why
    for idea in why.IDEAS:
        if idea != "deeper":
            assert course.lesson_for(idea), idea
