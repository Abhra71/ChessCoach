"""Build a page that shows the player's top mistake patterns on real boards from their own games.

Run:  python -m coach.review
Output: data/review.html  (user data, never committed) - open it in any browser.
"""
import collections
import html
import json
from datetime import date
from pathlib import Path

import chess
import chess.svg

from coach.patterns import classify

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "review.html"
EXAMPLES = 3
TOP = 3
LOSING_MATERIAL = ("left a piece hanging", "walked into a fork or trick")

# what each pattern means and the habit that fixes it, in plain words
ABOUT = {
    "left a piece hanging": (
        "You put a piece where it can be taken for free, or leave one there when it's attacked.",
        "Before every move, ask: after I move here, what can they take? Is every piece of mine safe?"),
    "missed a free capture": (
        "Your opponent left something unprotected and you didn't take it.",
        "After every move they make, ask: did they just leave something I can take?"),
    "walked into a fork or trick": (
        "Your move let them attack two things at once (or pin a piece), so you lose one a move later.",
        "Before you move, look at their checks and captures next move: can one piece hit two of mine?"),
    "walked into checkmate": (
        "Your move let them checkmate you.",
        "Before you move, look at every check they could give next."),
    "missed a checkmate": (
        "You could have checkmated them and didn't.",
        "Every move, look at all your checks first: one of them may end the game."),
    "stalemated a won game": (
        "You were winning, but left their king with no legal move while not in check: that's a draw.",
        "When they have only a king left, make sure your move leaves it at least one square to go to."),
}
NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
        chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"}


def move_number(r):
    return (r["ply"] - 1) // 2 + 1


def turning_point(r):
    """The move turned an even (or better) game into a lost one."""
    return r["cp_before"] >= -100 and r["cp_after"] <= -300


def pick_examples(rows, n=EXAMPLES):
    """Clearest examples: game-turning first, slower games before bullet, then biggest loss; one per game."""
    best = sorted(rows, key=lambda r: (not turning_point(r), r["time_class"] == "bullet", -r["loss"]))
    seen, out = set(), []
    for r in best:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
        if len(out) == n:
            break
    return out


def explain(pattern, r):
    """One or two plain sentences about this exact position (facts from the board, not guesses)."""
    board = chess.Board(r["fen"])
    me = board.turn
    best = board.parse_san(r["best"])
    best_piece = NAME[board.piece_at(best.from_square).piece_type]
    best_capture = board.piece_at(best.to_square)
    board.push_san(r["move"])
    reply = chess.Move.from_uci(r["reply_pv"][0]) if r["reply_pv"] else None
    if pattern == "left a piece hanging" and reply and board.is_capture(reply):
        taker = NAME[board.piece_at(reply.from_square).piece_type]
        taken = board.piece_at(reply.to_square)
        what = NAME[taken.piece_type] if taken else "a pawn"
        return (f"After {r['move']}, their {taker} on {chess.square_name(reply.from_square)} "
                f"can take your {what} on {chess.square_name(reply.to_square)}.")
    if pattern == "walked into a fork or trick" and reply:
        return (f"After {r['move']}, they answer {board.san(reply)} and you lose material "
                f"a move or two later, whatever you do.")
    if pattern == "missed a free capture" and best_capture:
        return (f"Their {NAME[best_capture.piece_type]} on {chess.square_name(best.to_square)} was there to take: "
                f"your {best_piece} takes it with {r['best']}.")
    if pattern == "missed a checkmate":
        return f"{r['best']} starts a forced checkmate."
    if pattern == "walked into checkmate" and reply:
        return f"After {r['move']}, they can start a forced checkmate with {board.san(reply)}."
    return f"Better was {r['best']}."


def board_svg(board, arrows, flip, lastmove=None):
    return chess.svg.board(board, orientation=chess.BLACK if flip else chess.WHITE, arrows=arrows, size=260,
                           lastmove=lastmove, coordinates=True)


def example_html(pattern, r):
    board = chess.Board(r["fen"])
    flip = board.turn == chess.BLACK
    mine = board.parse_san(r["move"])
    best = board.parse_san(r["best"])
    played = [chess.svg.Arrow(mine.from_square, mine.to_square, color="#d64545cc")]
    after = board.copy()
    after.push(mine)
    if r["reply_pv"]:
        reply = chess.Move.from_uci(r["reply_pv"][0])
        played.append(chess.svg.Arrow(reply.from_square, reply.to_square, color="#e8a33dcc"))
    better = [chess.svg.Arrow(best.from_square, best.to_square, color="#2e9e5bcc")]
    clock = f" · {int(r['clock'])}s left on your clock" if r.get("clock") is not None else ""
    side = "White" if not flip else "Black"
    return f"""
    <article class="ex">
      <p class="meta">Move {move_number(r)} · you are {side} · {r['time_class']}{clock} ·
        <a href="{html.escape(r['url'])}" target="_blank" rel="noopener">open game on chess.com</a></p>
      <p class="say">{html.escape(explain(pattern, r))}</p>
      <div class="boards">
        <figure>{board_svg(after, played, flip, lastmove=mine)}
          <figcaption><span class="dot red"></span>After your move {html.escape(r['move'])}
          {'<span class="dot amber"></span>their answer' if r['reply_pv'] else ''}</figcaption></figure>
        <figure>{board_svg(board, better, flip)}
          <figcaption><span class="dot green"></span>Better: {html.escape(r['best'])}</figcaption></figure>
      </div>
    </article>"""


def pieces_lost(rows, end_time, last=20):
    """Pieces given away per game (hanging + forks/tricks): over all games and over the last `last` games."""
    lost = collections.Counter(r["url"] for r in rows if classify(r) in LOSING_MATERIAL)
    order = sorted({r["url"] for r in rows}, key=lambda u: end_time.get(u, 0))
    recent = order[-last:]
    return (sum(lost[u] for u in order) / len(order), sum(lost[u] for u in recent) / len(recent), len(recent))


def build():
    rows = [json.loads(line) for line in open(ROOT / "data" / "moves.jsonl")]
    end_time = {g["url"]: g["end_time"] for f in (ROOT / "data").glob("games-*.json")
                for g in json.loads(f.read_text())["games"]}
    overall, recent, n_recent = pieces_lost(rows, end_time)
    player = (ROOT / "data" / "player.txt").read_text().strip()
    hits = collections.defaultdict(list)
    for r in rows:
        p = classify(r)
        if p:
            hits[p].append(r)
    games = len({r["url"] for r in rows})
    turned = collections.Counter()
    for url in {r["url"] for r in rows}:
        first = next((r for r in rows if r["url"] == url and turning_point(r)), None)
        if first:
            turned[classify(first) or "other"] += 1
    top = [p for p, _ in sorted(((p, rs) for p, rs in hits.items() if p in ABOUT), key=lambda kv: -len(kv[1]))][:TOP]

    sections = []
    for i, p in enumerate(top, 1):
        meaning, habit = ABOUT[p]
        rs = hits[p]
        n_games = len({r["url"] for r in rs})
        exs = "".join(example_html(p, r) for r in pick_examples(rs))
        sections.append(f"""
    <section>
      <h2><span class="num">{i}</span> You {html.escape(p)}</h2>
      <p class="stat"><b>{len(rs)}</b> times in <b>{n_games}</b> of your {games} games ·
        it was the move that lost an even game <b>{turned[p]}</b> times</p>
      <p>{html.escape(meaning)}</p>
      <p class="habit"><b>The habit that fixes it:</b> {html.escape(habit)}</p>
      {exs}
    </section>""")

    OUT.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Chess Review</title>
<style>
:root {{ --bg:#faf8f4; --card:#ffffff; --ink:#1f1d1a; --muted:#6b665e; --line:#e6e1d8; --accent:#2e7d57; --habit:#eef6f0; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#171614; --card:#211f1c; --ink:#ece8e1; --muted:#a39d93;
  --line:#34312c; --accent:#6cc497; --habit:#1d2a22; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:880px; margin:0 auto; padding:32px 16px 64px; }}
h1 {{ font-size:28px; margin:0 0 4px; }} h2 {{ font-size:22px; margin:0 0 6px; display:flex; gap:10px; align-items:center; }}
.sub, .meta, figcaption, .stat {{ color:var(--muted); font-size:14px; }}
.num {{ background:var(--accent); color:var(--bg); border-radius:50%; width:30px; height:30px; display:inline-grid;
  place-items:center; font-size:16px; flex:none; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:22px; margin:22px 0; }}
.habit {{ background:var(--habit); border-radius:10px; padding:10px 14px; }}
.ex {{ border-top:1px solid var(--line); margin-top:18px; padding-top:14px; }}
.say {{ font-weight:600; margin:4px 0 10px; }}
.boards {{ display:flex; flex-wrap:wrap; gap:18px; }}
figure {{ margin:0; }} figure svg {{ width:min(260px, 100%); height:auto; display:block; border-radius:6px; }}
figcaption {{ margin-top:6px; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
.dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
.red {{ background:#d64545; }} .amber {{ background:#e8a33d; }} .green {{ background:#2e9e5b; }}
a {{ color:var(--accent); }}
.score {{ display:flex; flex-wrap:wrap; gap:8px 28px; align-items:baseline; background:var(--card);
  border:1px solid var(--line); border-radius:14px; padding:16px 22px; }}
.score p {{ flex-basis:100%; margin:0; color:var(--muted); font-size:14px; }}
.big {{ font-size:30px; font-weight:700; color:var(--accent); margin-right:6px; }}
.ask {{ border:2px dashed var(--accent); border-radius:14px; padding:18px 22px; }}
</style></head><body><main>
<h1>Your chess review</h1>
<p class="sub">{html.escape(player)} · {games} games checked by Stockfish · {date.today():%d %b %Y}</p>
<p>These are the habits that lost you the most games, with real positions from your own games.
Red arrow: your move. Orange: what they could do next. Green: the better move.</p>
<div class="score"><div><span class="big">{overall:.1f}</span> pieces given away per game (all {games} games)</div>
<div><span class="big">{recent:.1f}</span> in your last {n_recent} games</div>
<p>This is the number to bring down. When it falls, your rating rises.</p></div>
{''.join(sections)}
<div class="ask"><b>Is this you?</b> Look at the boards. Do you remember moves like these?
Tell the coach: <i>yes</i>, <i>no</i>, or <i>some of them</i>.</div>
</main></body></html>""", encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(build())
