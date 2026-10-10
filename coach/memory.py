"""What the coach remembers about the player's practice and answers (kept in data/, never committed).

Practice uses boxes (Leitner): every right answer moves a position to the next box and the gap before it comes
back grows (1, 3, 7, 21, 60 days); a wrong answer sends it back to the start, to come back tomorrow.
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRACTICE = ROOT / "data" / "practice.jsonl"
VERDICTS = ROOT / "data" / "verdicts.jsonl"
GAPS = [1, 3, 7, 21, 60]  # days before a position comes back, by box
MASTERED = len(GAPS) + 1  # right this many times in a row: never comes back
LEARNED = 3  # right 3 times in a row, days apart: counted as learned on the page


def _append(path, entry):
    path.parent.mkdir(exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _read(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def record_practice(drill_id, kind, right, day=None):
    _append(PRACTICE, {"id": str(drill_id), "kind": kind, "right": bool(right),
                       "day": (day or date.today()).isoformat()})


def record_verdict(answer, day=None):
    _append(VERDICTS, {"answer": answer, "day": (day or date.today()).isoformat()})


def boxes():
    """drill id -> (box, day of last answer)."""
    state = {}
    for e in _read(PRACTICE):
        box, _ = state.get(e["id"], (0, None))
        state[e["id"]] = (min(box + 1, MASTERED) if e["right"] else 0, date.fromisoformat(e["day"]))
    return state


def is_due(box, last, today):
    if box >= MASTERED:
        return False
    gap = GAPS[box - 1] if box > 0 else 1
    return last + timedelta(days=gap) <= today


def choose(candidate_ids, n, today=None):
    """Up to n ids to practise today: missed ones that are due, then new ones (in the given order), then due reviews."""
    today = today or date.today()
    state = boxes()
    missed, new, review = [], [], []
    for cid in candidate_ids:
        if cid not in state:
            new.append(cid)
            continue
        box, last = state[cid]
        if is_due(box, last, today):
            (missed if box == 0 else review).append(cid)
    return (missed + new + review)[:n]


def practice_stats():
    """Simple numbers for the page: answers given, right ones, positions seen, positions learned."""
    entries = _read(PRACTICE)
    state = boxes()
    return {"answers": len(entries), "right": sum(e["right"] for e in entries),
            "positions": len(state), "learned": sum(1 for b, _ in state.values() if b >= LEARNED)}
