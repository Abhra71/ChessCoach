"""Pick ONE opening that suits the player, from the Lichess opening catalogue (coach/openings/*.tsv, CC0).

How it chooses (engine and data, no AI):
- what the player already plays (their first move as White, their answer to e4/d4 as Black) and how it scores;
- the catalogue's main lines that start the same way (as White) or answer the move they meet most (as Black);
- sound only: Stockfish checks the position at the end of the line;
- style: a player who leaves pieces loose gets solid systems first (fewer early tactics).
Every move of the line gets a plain-words idea, worked out from the move itself (develops a knight, castles...).
"""
import collections
import csv
import io
import json
import re
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from coach.paths import DATA

CATALOGUE = Path(__file__).resolve().parent / "openings"
EVALS = DATA / "opening-evals.json"
SOLID = ("Italian Game", "Caro-Kann", "Queen's Gambit Declined", "London System", "Slav Defense", "French Defense",
         "Four Knights", "Scotch Game", "Petrov", "Philidor", "Colle", "English Opening")  # best first for beginners
MAIN = ("Main Line", "Classical Variation", "Classical", "Giuoco Piano", "Modern Variation", "Exchange Variation")
SHARP = ("Gambit", "Sicilian", "King's Gambit", "Alekhine", "Scandinavian", "Dutch", "Benoni", "Grunfeld", "Budapest",
         "Englund", "Latvian", "Elephant", "Damiano", "Halloween", "Grob", "Polish", "Owen", "Borg", "St. George")
CENTRE = {chess.D4, chess.E4, chess.D5, chess.E5}


def catalogue():
    """[(eco, name, [san...])] for every line in the catalogue."""
    out = []
    for f in sorted(CATALOGUE.glob("*.tsv")):
        for row in csv.DictReader(io.StringIO(f.read_text(encoding="utf-8")), delimiter="\t"):
            sans = [t for t in row["pgn"].split() if not re.match(r"^\d+\.", t)]
            out.append((row["eco"], row["name"], sans))
    return out


BLACK_SOLID = ("Caro-Kann", "Queen's Gambit Declined", "Slav Defense", "French Defense", "Petrov", "Philidor")


def style(name):
    if any(s in name for s in SHARP) and "Declined" not in name:  # a gambit declined is the solid answer
        return "sharp"
    return "solid" if any(s in name for s in SOLID) else "normal"


def family(name):
    return name.split(":")[0].strip()


def idea(board, move):
    """What a move does, in plain words, worked out from the position."""
    piece, san = board.piece_at(move.from_square), board.san(move)
    if board.is_castling(move):
        return "Castle: your king is safe and your rook comes into play."
    if board.is_capture(move):
        return f"{san}: take back, so the material stays even."
    if piece.piece_type == chess.PAWN and move.to_square in CENTRE:
        return f"{san}: a pawn in the centre, so your pieces have room."
    if piece.piece_type == chess.PAWN:
        return f"{san}: a pawn move that supports your centre or opens a path for a piece."
    if piece.piece_type in (chess.KNIGHT, chess.BISHOP) and chess.square_rank(move.from_square) in (0, 7):
        name = "knight" if piece.piece_type == chess.KNIGHT else "bishop"
        return f"{san}: develop your {name} towards the centre."
    return f"{san}: improve a piece."


def teach(sans, side):
    """The line with an idea for each of the player's own moves."""
    board, steps = chess.Board(), []
    for i, san in enumerate(sans):
        move = board.parse_san(san)
        mine = (i % 2 == 0) == (side == "white")
        steps.append({"san": san, "uci": move.uci(), "mine": mine, "idea": idea(board, move) if mine else None})
        board.push(move)
    return {"steps": steps, "fen": board.fen()}


def habits(games, player):
    """What the player plays: {('white', 'e4'): [wins, games], ('black', 'e4', 'Nf6'): [...]}."""
    seen = collections.defaultdict(lambda: [0, 0])
    for g in games:
        side = "white" if g["white"]["username"].lower() == player.lower() else "black"
        try:
            sans = [m for m in _sans(g["pgn"])[:2]]
        except ValueError:
            continue
        if not sans:
            continue
        key = (side, sans[0], sans[1] if len(sans) > 1 else None)
        seen[key][0] += g[side]["result"] == "win"
        seen[key][1] += 1
    return dict(seen)


def _sans(pgn):
    game = chess.pgn.read_game(io.StringIO(pgn))
    board, out = game.board(), []
    for move in game.mainline_moves():
        out.append(board.san(move))
        board.push(move)
    return out


def _eval(fen, side, engine):
    cache = json.loads(EVALS.read_text()) if EVALS.exists() else {}
    if fen not in cache:
        info = engine.analyse(chess.Board(fen), chess.engine.Limit(depth=12))
        cache[fen] = info["score"].white().score(mate_score=10000)
        EVALS.parent.mkdir(parents=True, exist_ok=True)
        EVALS.write_text(json.dumps(cache))
    return cache[fen] if side == "white" else -cache[fen]


def _rank(name, loose_pieces, side):
    """Solid openings first for a player who leaves pieces loose; main lines before side lines."""
    kind = style(name)
    best = BLACK_SOLID if side == "black" else SOLID
    solid = next((i for i, f in enumerate(best) if f in name), len(best))
    main = next((i for i, m in enumerate(MAIN) if name.endswith(m)), len(MAIN) + (":" in name))  # named main line, root, side line
    order = {"solid": 0, "normal": 1, "sharp": 2} if loose_pieces else {"solid": 1, "normal": 0, "sharp": 2}
    return (order[kind], solid, main)


def suggest(games, player, loose_pieces, engine, avoid=()):
    """The one opening to learn next, or None. loose_pieces: the player's main habit is losing material."""
    seen = habits(games, player)
    if not seen:
        return None
    # group by side and the first move of the game; where it scores under half and is played often, help first
    groups = collections.defaultdict(lambda: [0, 0, collections.Counter()])
    for (side, first, second), (wins, played) in seen.items():
        g = groups[(side, first)]
        g[0] += wins; g[1] += played; g[2][second] += played
    need = sorted(groups.items(), key=lambda kv: (kv[1][0] / kv[1][1] >= 0.5, -kv[1][1]))
    for (side, first), (wins, played, seconds) in need:
        if played < 3:
            continue
        second = seconds.most_common(1)[0][0]
        if side == "white":  # teach the line against the reply they meet most
            fits = lambda sans: sans[0] == first and len(sans) > 1 and sans[1] == second
        else:  # a better answer to the move they meet, unless their own answer already works
            mine = seen.get((side, first, second), [0, 1])
            fits = lambda sans: sans[0] == first and len(sans) > 1 and not (sans[1] == second and mine[0] / mine[1] < 0.5)
        options = [(eco, name, sans) for eco, name, sans in catalogue()
                   if 5 <= len(sans) <= 14 and fits(sans) and name.count(":") <= 1 and "," not in name
                   and family(name) not in avoid]
        options.sort(key=lambda o: (_rank(o[1], loose_pieces, side), -len(o[2])))
        for eco, name, sans in options[:25]:
            lesson = teach(sans, side)
            if _eval(lesson["fen"], side, engine) >= -60:  # sound: no worse than a slight disadvantage
                return {"id": f"opening:{eco}:{name}", "kind": "opening", "title": f"{name} (as {side.title()})",
                        "name": name, "eco": eco, "side": side, "style": style(name), "against": first if side == "black" else second,
                        "current": second if side == "black" else None, "score": [wins, played], **lesson}
    return None
