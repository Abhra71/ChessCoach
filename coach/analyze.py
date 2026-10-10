"""Check every move the player made with Stockfish and save one record per move.

Run:  python -m coach.analyze   (games in data/ not checked yet, for the player in data/player.txt)
      python -m coach.analyze --all   (check every game again)
Output: data/moves.jsonl  (user data, never committed)
"""
import glob
import io
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import chess
import chess.engine
import chess.pgn

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine" / "stockfish" / "stockfish-windows-x86-64-universal.exe"
MOVES = ROOT / "data" / "moves.jsonl"
CHECKED = ROOT / "data" / "checked.txt"
DEPTH = 14
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def win_chance(cp):
    """Lichess formula: centipawns -> chance of winning, 0..100."""
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def score_cp(score):
    return score.score(mate_score=10000)


def material(board, color):
    return sum(VALUE[p.piece_type] for p in board.piece_map().values() if p.color == color)


def analyse_game(game_json, player):
    game = chess.pgn.read_game(io.StringIO(game_json["pgn"]))
    me = chess.WHITE if game_json["white"]["username"].lower() == player else chess.BLACK
    out = []
    with chess.engine.SimpleEngine.popen_uci(str(ENGINE)) as eng:
        eng.configure({"Threads": 1, "Hash": 64})
        board = game.board()
        node = game
        while node.variations:
            nxt = node.variations[0]
            move = nxt.move
            if board.turn == me:
                before = eng.analyse(board, chess.engine.Limit(depth=DEPTH))
                best = before["pv"][0]
                cp_before = score_cp(before["score"].pov(me))
                mat_before = material(board, me) - material(board, not me)
                san, best_san = board.san(move), board.san(best)
                fen = board.fen()
                board.push(move)
                if board.is_game_over():
                    after_score = 0 if not board.is_checkmate() else 10000
                    reply_pv = []
                else:
                    after = eng.analyse(board, chess.engine.Limit(depth=DEPTH))
                    after_score = score_cp(after["score"].pov(me))
                    reply_pv = [m.uci() for m in after.get("pv", [])[:4]]
                    mate_against = after["score"].pov(me).is_mate() and after["score"].pov(me).mate() < 0
                out.append({
                    "url": game_json["url"], "time_class": game_json["time_class"],
                    "color": "white" if me else "black", "ply": board.ply(), "fen": fen,
                    "move": san, "best": best_san, "best_is_capture": chess.Board(fen).is_capture(best),
                    "best_mates": before["score"].pov(me).is_mate() and before["score"].pov(me).mate() > 0,
                    "cp_before": cp_before, "cp_after": after_score,
                    "loss": round(win_chance(cp_before) - win_chance(after_score), 1),
                    "allows_mate": bool(reply_pv) and mate_against,
                    "reply_pv": reply_pv, "mat_before": mat_before,
                    "clock": nxt.clock(), "stalemate": board.is_stalemate(),
                })
                node = nxt
                continue
            board.push(move)
            node = nxt
    return out


def checked_games():
    """URLs of games already checked (kept in data/checked.txt, so games with no moves of ours are skipped too)."""
    if CHECKED.exists():
        return set(CHECKED.read_text().split())
    if MOVES.exists():  # older data from before checked.txt existed
        return {json.loads(line)["url"] for line in open(MOVES)}
    return set()


def main():
    player = (ROOT / "data" / "player.txt").read_text().strip().lower()
    redo = "--all" in sys.argv
    done_urls = set() if redo else checked_games()
    games = [g for f in sorted(glob.glob(str(ROOT / "data" / "games-*.json")))
             for g in json.load(open(f))["games"]
             if g.get("rules") == "chess" and g["url"] not in done_urls]
    if not games:
        print("no new games to check", file=sys.stderr)
        CHECKED.write_text("\n".join(sorted(done_urls)) + "\n")
        return 0
    mode = "w" if redo else "a"
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool, open(MOVES, mode) as fh:
        for done, (game, rows) in enumerate(zip(games, pool.map(analyse_game, games, [player] * len(games))), 1):
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            done_urls.add(game["url"])
            print(f"\r{done}/{len(games)} games", end="", file=sys.stderr, flush=True)
    CHECKED.write_text("\n".join(sorted(done_urls)) + "\n")
    print(f"\nchecked {len(games)} new games -> {MOVES}", file=sys.stderr)
    return len(games)


if __name__ == "__main__":
    main()
