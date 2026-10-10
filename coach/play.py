"""Play the Coach: a game against Stockfish at the player's level, with the coach watching and helping live.

All inside our own app (never on chess.com, where fair-play rules forbid help during any game).
The opponent is weakened on purpose: Stockfish's own weakest setting is about 1300 Elo, far above a beginner,
so at low levels the coach picks among the engine's top moves with some randomness, and sometimes a slip.
"""
import math
import random

import chess
import chess.engine

from coach.analyze import score_cp, win_chance
from coach.facts import describe_move, loose_pieces

LEVELS = {  # level -> (search depth, how many top moves it chooses from, randomness, chance of a slip)
    1: (4, 8, 220, 0.25), 2: (5, 6, 160, 0.18), 3: (6, 5, 110, 0.12), 4: (7, 4, 80, 0.08), 5: (8, 4, 55, 0.05),
    6: (10, 3, 35, 0.03), 7: (12, 3, 20, 0.015), 8: (14, 2, 10, 0.0), 9: (16, 2, 4, 0.0), 10: (18, 1, 1, 0.0),
}
ABOUT_ELO = {1: 300, 2: 450, 3: 600, 4: 750, 5: 900, 6: 1100, 7: 1300, 8: 1500, 9: 1800, 10: 2200}
MISTAKE = 25  # winning chance lost (0..100) that makes the coach step in


def level_for(rating):
    """The level closest to the player's chess.com rating, a little above it to stretch them."""
    target = (rating or 400) + 100
    return min(ABOUT_ELO, key=lambda lv: abs(ABOUT_ELO[lv] - target))


def legal(board):
    return {m.uci(): board.san(m) for m in board.legal_moves}


def state(board):
    over = board.outcome()
    return {"fen": board.fen(), "legal": legal(board), "turn": "white" if board.turn else "black",
            "check": board.is_check(), "over": bool(over),
            "result": None if not over else ("checkmate" if over.termination == chess.Termination.CHECKMATE else over.termination.name.lower()),
            "winner": None if not over or over.winner is None else ("white" if over.winner else "black")}


def engine_move(engine, board, level, rng=random):
    depth, width, spread, slip = LEVELS[level]
    infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=width)
    options = [(i["pv"][0], score_cp(i["score"].pov(board.turn))) for i in infos if i.get("pv")]
    if rng.random() < slip and board.legal_moves.count() > 1:  # a human-like slip: any legal move, now and then
        return rng.choice(list(board.legal_moves))
    best = max(cp for _, cp in options)
    weights = [math.exp((cp - best) / spread) for _, cp in options]
    return rng.choices([m for m, _ in options], weights=weights)[0]


def warnings(board, me):
    """What the coach says before the player moves: their pieces that can be taken, checks against them."""
    out = []
    loose = loose_pieces(board, me)
    if loose:
        out.append("Careful: your " + ", ".join(loose) + (" is" if len(loose) == 1 else " are") + " not safe.")
    if board.is_check():
        out.append("You're in check.")
    return out


def judge(engine, before, move, me, depth=12):
    """How good the player's move was: winning chance lost, and the plain facts if it was a mistake."""
    limit = chess.engine.Limit(depth=depth)
    best_info = engine.analyse(before, limit)
    best = best_info["pv"][0]
    chance_before = win_chance(score_cp(best_info["score"].pov(me)))
    after = before.copy()
    after.push(move)
    if after.is_game_over():
        chance_after = 100.0 if after.is_checkmate() else 50.0
    else:
        chance_after = win_chance(score_cp(engine.analyse(after, limit)["score"].pov(me)))
    loss = round(chance_before - chance_after)
    verdict = {"loss": loss, "mistake": loss >= MISTAKE and move != best}
    if verdict["mistake"]:
        verdict.update(played=before.san(move), played_does=describe_move(before, move),
                       best=before.san(best), best_uci=best.uci(), best_does=describe_move(before, best))
    return verdict


def hint(engine, board, depth=14):
    """Hints in two steps: which piece to look at, then the move itself."""
    best = engine.analyse(board, chess.engine.Limit(depth=depth))["pv"][0]
    piece = board.piece_at(best.from_square)
    from coach.review import NAME
    return {"piece_square": chess.square_name(best.from_square),
            "piece": f"your {NAME[piece.piece_type]} on {chess.square_name(best.from_square)}",
            "move": board.san(best), "uci": best.uci(), "does": describe_move(board, best)}


class Game:
    """One game against the coach, kept on the coach's side (one at a time)."""

    def __init__(self, color, level):
        self.me = chess.WHITE if color == "white" else chess.BLACK
        self.level = level if level in LEVELS else 3
        self.board = chess.Board()
        self.mistakes = 0
        self.takebacks = 0

    def view(self, **extra):
        last = self.board.peek().uci() if self.board.move_stack else None
        return {**state(self.board), "color": "white" if self.me else "black", "level": self.level,
                "about_elo": ABOUT_ELO[self.level], "last": last, "mistakes": self.mistakes,
                "takebacks": self.takebacks, "moves": self._sans(), **extra}

    def _sans(self):
        b, out = self.board.root(), []  # replay from where this game started
        for m in self.board.move_stack:
            out.append(b.san(m))
            b.push(m)
        return out

    def reply(self, engine, rng=random):
        """The coach's opponent moves, then the coach looks at what the player now faces."""
        if self.board.is_game_over() or self.board.turn == self.me:
            return self.view(warnings=[])
        move = engine_move(engine, self.board, self.level, rng)
        san = self.board.san(move)
        self.board.push(move)
        return self.view(their_move=san, warnings=warnings(self.board, self.me) if not self.board.is_game_over() else [])

    def player_move(self, engine, uci, coach=True):
        move = chess.Move.from_uci(uci)
        if self.board.turn != self.me or move not in self.board.legal_moves:
            raise ValueError("That move isn't legal here.")
        before = self.board.copy()
        verdict = judge(engine, before, move, self.me) if coach else {"mistake": False}
        self.board.push(move)
        if verdict["mistake"]:
            self.mistakes += 1
            return self.view(verdict=verdict, waiting=True)  # the player chooses: take it back, or play on
        return self.reply(engine)

    def takeback(self):
        if self.board.move_stack and self.board.turn != self.me:
            self.board.pop()
            self.takebacks += 1
        return self.view(warnings=warnings(self.board, self.me))
