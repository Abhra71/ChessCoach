"""Your game of the week as a short 3D film (1.0): the script the 3D scene plays (coach/ui/film.js).

Not the whole game at one speed: quiet moves go by quickly, and the film slows down only for the two or three moves
that won it, with a caption ("Move 23. Your bishop takes their queen on f7, check."), and the last move. Seen mostly
from above, like a broadcast, so it can be followed. The moves come from the real game through python-chess, so the
film can't show a wrong move.
"""
import io
from datetime import datetime
from pathlib import Path

import chess
import chess.pgn

from coach import insights
from coach.blindfold import NAME

HIGHLIGHTS = 3  # moments that win the game, at most, besides the last move
QUIET_SECONDS = 34  # all the quiet moves together take about this long (20 Oct, the owner: "slightly slower")
SAVED = Path.home() / "Videos" / "Knightwise"  # next to the week's picture in Pictures\Knightwise


def _turning_points(rows, n):
    """Your moves that mattered most for the win: you found the engine's move and it gained the most, against how it
    stood after your previous move (their slip, punished). rows: the checked moves of the game, by ply."""
    out, prev = [], None
    for r in sorted(rows, key=lambda r: r["ply"]):
        gain = (r["cp_after"] - prev) if prev is not None else 0
        if r["move"] == r["best"] and gain > 150:
            out.append((gain, r["ply"]))
        prev = r["cp_after"]
    return sorted(p for _, p in sorted(out, reverse=True)[:n])


def _caption(board, move, ply):
    """What the film says at a highlight: "Move 23. Your bishop takes their queen on f7: check!"."""
    piece = board.piece_at(move.from_square)
    sq = chess.square_name(move.to_square)
    taken = board.piece_at(move.to_square)
    if board.is_en_passant(move):
        taken = chess.Piece(chess.PAWN, not piece.color)
    if board.is_castling(move):
        words = f"You castle {'short' if chess.square_file(move.to_square) == 6 else 'long'}"
    elif taken:
        words = f"Your {NAME[piece.piece_type]} takes their {NAME[taken.piece_type]} on {sq}"
    else:
        words = f"Your {NAME[piece.piece_type]} goes to {sq}"
    if move.promotion:
        words += f" and becomes a {NAME[move.promotion]}"
    board.push(move)
    end = ": checkmate!" if board.is_checkmate() else ": check!" if board.is_check() else "."
    board.pop()
    return f"Move {ply // 2 + 1}. {words}{end}"


def script(gid):
    """{title, you, white, black, result, date, moves: [{from, to, san, capture, rook, promo, slow, caption}], end}
    for one of your games, or None."""
    g = next((g for g in insights._games() if g["url"].rstrip("/").split("/")[-1] == str(gid)), None)
    player = insights._player()
    if not g or not player:
        return None
    game = chess.pgn.read_game(io.StringIO(g.get("pgn") or ""))
    if game is None:
        return None
    color, other = insights._side(g, player)
    you = chess.WHITE if color == "white" else chess.BLACK
    rows = insights._moves().get(g["url"], [])
    result = insights._result(g, color)
    turning = set(_turning_points(rows, HIGHLIGHTS)) if result != "loss" else set()
    played = list(game.mainline_moves())
    quiet = max(1, len(played) - len(turning) - 1)
    board, moves = game.board(), []
    for ply, m in enumerate(played):
        last = ply == len(played) - 1
        mine = board.turn == you
        step = {"from": chess.square_name(m.from_square), "to": chess.square_name(m.to_square), "san": board.san(m)}
        if board.is_en_passant(m):
            step["capture"] = chess.square_name(chess.square(chess.square_file(m.to_square), chess.square_rank(m.from_square)))
        elif board.is_capture(m):
            step["capture"] = step["to"]
        if board.is_castling(m):
            rank = "1" if board.turn == chess.WHITE else "8"
            short = chess.square_file(m.to_square) == 6
            step["rook"] = [("h" if short else "a") + rank, ("f" if short else "d") + rank]
        if m.promotion:
            step["promo"] = chess.piece_symbol(m.promotion)
        if mine and (ply + 1 in turning or last):
            step["slow"] = True
            step["caption"] = _caption(board, m, ply)
        board.push(m)
        moves.append(step)
    how = (game.headers.get("Termination") or "").lower()  # chess.com: "gushynanda won by resignation"
    why = (" They resigned." if "resignation" in how else " On time." if "time" in how
           else " They left the game." if "abandon" in how else "")
    end = ("Checkmate. You won." if board.is_checkmate() and result == "win" else
           f"You won.{why}" if result == "win" else "A draw." if result == "draw" else "They won this one.")
    return {"title": "Your game of the week", "you": color, "white": g["white"]["username"], "black": g["black"]["username"],
            "opponent": g[other]["username"], "result": result, "end": end, "moves": moves, "quiet": min(1.0, max(0.55, QUIET_SECONDS / quiet)),
            "date": datetime.fromtimestamp(g["end_time"]).strftime("%d %b %Y"), "id": str(gid)}


def week_game():
    """The id of this week's best game (coach/progress.py's story), or None."""
    from coach import progress
    try:
        s = progress.page().get("story") or {}
    except Exception:  # never let the film stop the progress page
        return None
    best = s.get("best") or {}
    return best.get("id") if best.get("result") == "win" else None


def save(data, gid):
    """Keep a recorded film (webm) in Videos/Knightwise; returns the file's path."""
    SAVED.mkdir(parents=True, exist_ok=True)
    out = SAVED / f"knightwise-game-{''.join(c for c in str(gid) if c.isalnum())[:20]}.webm"
    out.write_bytes(data)
    return out
