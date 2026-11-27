"""Bug hunt 27 Nov: the game check appends to data/moves.jsonl while the app reads it. A half-written last line used
to crash the reader, so chess.com's instant review got no answer and stopped looking for the game just finished."""
import json

from coach import analyze, insights, service

ROW = dict(url="https://www.chess.com/game/live/42", color="white", stalemate=False, cp_before=0, cp_after=-800,
           best_mates=False, allows_mate=False, best_is_capture=False, mat_before=8, loss=45,
           fen="4k3/8/3p4/8/3Q4/8/8/4K3 w - - 0 1", move="Qe5", best="Qd5", reply_pv=["d6e5"], ply=31)


def half_written(tmp_path):
    path = tmp_path / "moves.jsonl"
    whole = json.dumps(ROW) + "\n"
    path.write_text(whole + whole.replace('"ply": 31', '"ply": 33') + json.dumps(dict(ROW, ply=35))[:40], encoding="utf-8")
    return path


def test_a_half_written_last_line_is_skipped(tmp_path):
    rows = analyze.read_rows(half_written(tmp_path))
    assert [r["ply"] for r in rows] == [31, 33]


def test_the_review_still_answers_while_a_check_is_writing(tmp_path, monkeypatch):
    half_written(tmp_path)
    monkeypatch.setattr(service, "DATA", tmp_path)
    assert [r["ply"] for r in service.Moments().get("42")] == [31, 33]


def test_the_app_pages_still_read_while_a_check_is_writing(tmp_path, monkeypatch):
    half_written(tmp_path)
    monkeypatch.setattr(insights, "DATA", tmp_path)
    monkeypatch.setattr(insights, "_CACHE", {"mtime": None, "rows": None})
    rows = insights._moves()
    assert [r["ply"] for r in rows[ROW["url"]]] == [31, 33]
