"""Strong players' games, sorted by pawn structure (0.11): the plans behind the moves.

Source: the Lichess Elite Database (database.nikonoel.fr), Lichess games between players rated 2,300 to 2,500+; Lichess
games are CC0. Built once, offline, from a few monthly files: games are sorted into the pawn structures club players
meet most (and the ones the player's own repertoire leads to), and for each one we keep a few model games won by the
structure's plan, plus "find the strong player's move" positions where Stockfish agrees the move was a good one.
Only the result is kept (coach/library/elite.json, a few hundred KB): ratings and moves, no player names. The
download itself is deleted afterwards.

Run:  python -I <runner> <zip files...>   (the runner adds this project to the path; see docs/ELITE.md)
"""
import collections
import io
import json
import sys
import zipfile
from pathlib import Path

import chess
import chess.engine
import chess.pgn

OUT = Path(__file__).resolve().parent / "library" / "elite.json"
CHECK_AT = (24, 28, 32)  # the structure must hold at moves 12, 14 and 16
MIN_ELO = 2400
GAMES_PER = 6  # model games kept per structure
DRILLS_PER = 10  # "find the move" positions per structure
CANDIDATES = 200  # games looked at per structure before stopping
GOOD_CP = 40  # the strong player's move counts when Stockfish has it within 40 centipawns of its best

# plan text in our own words: what each side aims for in this structure
STRUCTURES = {
    "iqp": {"name": "The isolated queen's pawn", "owner": "white",
            "plan": {"owner": "You have space and open lines: put your pieces on active squares, aim at the king, and look "
                              "for the d4-d5 break. Trades help the other side.",
                     "other": "Stop the pawn: put a piece (best a knight) on the square in front of it, trade pieces, and "
                              "win the pawn in the endgame."}},
    "carlsbad": {"name": "The Carlsbad structure (Queen's Gambit Declined)", "owner": "white",
                 "plan": {"owner": "The minority attack: push the b-pawn to b5 to leave Black a weak pawn on c6, then attack it.",
                          "other": "Play on the kingside: a knight to e4, rooks to the e-file, and sometimes ...f5. Meet b5 "
                                   "calmly with ...c6xb5 or ...cxb5."}},
    "caro": {"name": "The Caro-Kann structure", "owner": "black",
             "plan": {"owner": "Solid and patient: finish developing, keep the light-squared bishop active outside the "
                               "pawns, and strike at d4 with ...c5 at the right moment.",
                      "other": "Use your extra space: a knight to e5, pressure on the kingside, and the queen and bishop "
                               "aimed at Black's king."}},
    "italian": {"name": "The slow Italian", "owner": "white",
                "plan": {"owner": "Manoeuvre first: knight b1-d2-f1-g3, h3 and a4, then the d3-d4 break when your pieces are ready.",
                         "other": "Mirror the plan: ...a6 and ...Ba7 to keep the bishop, a knight to g6, and ...d5 when you can."}},
    "sicilian": {"name": "The open Sicilian", "owner": "white",
                 "plan": {"owner": "Use your lead in development: pieces to good squares quickly, then attack the king, "
                                   "often with f4 or g4.",
                          "other": "Play on the half-open c-file and the queenside (...b5), and the ...d5 break frees your game."}},
    "french": {"name": "The French pawn chain", "owner": "white",
               "plan": {"owner": "Your pawn on e5 gives you space on the kingside: support it, and attack there with f4-f5.",
                        "other": "Hit the chain at its base: ...c5 against d4, then ...f6 against e5."}},
    "kid": {"name": "The closed King's Indian", "owner": "white",
            "plan": {"owner": "Attack on the queenside: c4-c5 to open lines towards Black's queenside.",
                     "other": "Attack the king: ...f5, then ...f4 and ...g5, pieces towards White's king."}},
    "hanging": {"name": "Hanging pawns", "owner": "white",
                "plan": {"owner": "Keep the two pawns side by side; push one of them only when it wins something.",
                         "other": "Pressure them until one has to step forward, then blockade the square in front of it."}},
}


def _files(board, color):
    out = collections.defaultdict(list)
    for sq in board.pieces(chess.PAWN, color):
        out[chess.square_file(sq)].append(sq)
    return out


def _has(board, color, name):
    p = board.piece_at(chess.parse_square(name))
    return bool(p and p.piece_type == chess.PAWN and p.color == color)


def structure(board):
    """The structure on the board (with the side that owns it), or None. White's names, mirrored for Black."""
    W, B = chess.WHITE, chess.BLACK
    for owner, me, them, r in ((W, W, B, ""), (B, B, W, "m")):
        mf, tf = _files(board, me), _files(board, them)
        sq = lambda s: s if not r else s[0] + str(9 - int(s[1]))  # mirror a square for Black
        if mf.get(3) == [chess.parse_square(sq("d4"))] and 2 not in mf and 4 not in mf and 3 not in tf:
            return "iqp", owner
        if _has(board, me, sq("c4")) and _has(board, me, sq("d4")) and 1 not in mf and 4 not in mf \
                and 2 not in tf and 3 not in tf:
            return "hanging", owner
    if _has(board, W, "d4") and 2 not in _files(board, W) and _has(board, B, "c6") and _has(board, B, "d5") \
            and 4 not in _files(board, B) and 1 in _files(board, W):
        return "carlsbad", W
    if _has(board, W, "d4") and 4 not in _files(board, W) and _has(board, B, "c6") and _has(board, B, "e6") \
            and 3 not in _files(board, B):
        return "caro", B
    if all(_has(board, W, s) for s in ("c3", "d3", "e4")) and _has(board, B, "e5") and \
            (_has(board, B, "d6") or _has(board, B, "d7")):
        return "italian", W
    if _has(board, W, "e4") and 3 not in _files(board, W) and 2 not in _files(board, B) and 3 in _files(board, B):
        return "sicilian", W
    if all(_has(board, W, s) for s in ("d4", "e5")) and all(_has(board, B, s) for s in ("d5", "e6")):
        return "french", W
    if all(_has(board, W, s) for s in ("c4", "d5", "e4")) and all(_has(board, B, s) for s in ("d6", "e5")):
        return "kid", W
    return None


def _games(paths):
    for p in paths:
        z = zipfile.ZipFile(p)
        for name in z.namelist():
            f = io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
            while True:
                g = chess.pgn.read_game(f)
                if g is None:
                    break
                yield g


def _wanted(g):
    h = g.headers
    try:
        base = int(h.get("TimeControl", "0+0").split("+")[0])
        return h.get("Result") in ("1-0", "0-1") and base >= 180 and h.get("Termination") == "Normal" \
            and min(int(h["WhiteElo"]), int(h["BlackElo"])) >= MIN_ELO
    except (ValueError, KeyError):
        return False


def collect(paths, limit=CANDIDATES):
    """Games per structure where the structure holds at moves 12, 14 and 16 and its owner... either side won."""
    found = collections.defaultdict(list)
    for g in _games(paths):
        if all(len(found[k]) >= limit for k in STRUCTURES):
            break
        if not _wanted(g):
            continue
        moves = list(g.mainline_moves())
        if len(moves) < 60:
            continue
        board, seen = g.board(), []
        for i, m in enumerate(moves[:max(CHECK_AT)]):
            board.push(m)
            if i + 1 in CHECK_AT:
                seen.append(structure(board))
        if seen and seen[0] and all(s == seen[0] for s in seen) and len(found[seen[0][0]]) < limit:
            key, owner = seen[0]
            winner = chess.WHITE if g.headers["Result"] == "1-0" else chess.BLACK
            found[key].append({"moves": [m.uci() for m in moves[:90]], "owner": "white" if owner else "black",
                               "winner": "white" if winner else "black", "elo": [int(g.headers["WhiteElo"]), int(g.headers["BlackElo"])],
                               "tc": g.headers.get("TimeControl"), "plies": len(moves)})
    return found


ALSO_GOOD = "Also a good move, Stockfish agrees. But the strong player chose a move that follows the plan: find it."


def plan_step(board, played, also_good, plan):
    """The strong player's move is the answer. Moves Stockfish rates about as well aren't called wrong: they're
    marked good-but-not-it, so the training is about the plan, not about any decent move."""
    from coach import drills
    st = drills.step(board, {played}, lambda mv: f"Not the strong player's move. Think about the plan: {plan}",
                     close=also_good)
    for u, entry in st["moves"].items():
        if entry.get("close"):
            entry["say"] = ALSO_GOOD
    return st


def _drills(engine, game, side, plan, structure_name):
    """Positions from moves 13 to 30 where the winner's move was quiet and Stockfish agrees it's good."""
    from coach import drills
    board, out = chess.Board(), []
    for i, u in enumerate(game["moves"]):
        m = chess.Move.from_uci(u)
        mover = "white" if board.turn else "black"
        if 24 <= i < 60 and mover == side and not board.is_capture(m) and not board.gives_check(m) and len(out) < 2:
            infos = engine.analyse(board, chess.engine.Limit(depth=12), multipv=4)
            scores = {inf["pv"][0]: inf["score"].pov(board.turn).score(mate_score=10000) for inf in infos if inf.get("pv")}
            top = max(scores.values())
            board.push(m)
            mine = -engine.analyse(board, chess.engine.Limit(depth=12))["score"].pov(board.turn).score(mate_score=10000)
            board.pop()
            if top - mine <= GOOD_CP and abs(top) < 250:
                st = plan_step(board, m, {x for x, s in scores.items() if top - s <= GOOD_CP} - {m}, plan)
                out.append({"id": f"elite:{structure_name}:{i}:{u}", "kind": "puzzle", "flip": side == "black",
                            "pattern": "", "hint": plan, "intro": f"You are {side.capitalize()}. Find the strong player's move.",
                            "where": f"{STRUCTURES[structure_name]['name']}: a game between players rated "
                                     f"{game['elo'][0]:,} and {game['elo'][1]:,}, move {i // 2 + 1}",
                            "start": drills.squares(board), "last": None, "steps": [st], "played": board.san(m)})
        board.push(m)
    return out


def build(paths, engine):
    found = collect(paths)
    lib = {}
    for key, games in found.items():
        s = STRUCTURES[key]
        # model games: the side that owns the structure won (its plan worked), the longest decisive ones first
        model = sorted([g for g in games if g["winner"] == g["owner"]], key=lambda g: -g["plies"])[:GAMES_PER]
        other = sorted([g for g in games if g["winner"] != g["owner"]], key=lambda g: -g["plies"])[:GAMES_PER // 2]
        drills_ = []
        for g in model + other:
            side = g["winner"]
            plan = s["plan"]["owner" if side == g["owner"] else "other"]
            if len(drills_) < DRILLS_PER:
                drills_ += _drills(engine, g, side, plan, key)
        lib[key] = {**s, "found": len(games), "games": model + other, "drills": drills_[:DRILLS_PER]}
        print(f"{key:10} {len(games):4} games, {len(model)} won by the plan, {len(drills_[:DRILLS_PER])} positions", file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "Lichess Elite Database (database.nikonoel.fr), Lichess games, CC0",
                               "structures": lib}))
    return lib


def library():
    try:
        return json.loads(OUT.read_text())["structures"]
    except (OSError, ValueError, KeyError):
        return {}


def main(argv):
    from coach.analyze import open_engine
    with open_engine() as eng:
        eng.configure({"Threads": 4, "Hash": 128})
        build(argv, eng)


if __name__ == "__main__":
    main(sys.argv[1:])
