"""The human-move model (1.0): Maia-3, which plays like a human of any rating.

Maia-3 (University of Toronto, CSSLab, AGPL-3.0; github.com/CSSLab/maia3) is a small transformer trained on Lichess
games from January 2023 to July 2025. Given a position and a rating, it answers "what would a player of this rating
play here?", mistakes included, with a chance for every legal move. It replaced Maia 1 (nine fixed levels from 1,100
to 1,900, run by Leela) on 20 Oct 2026: one model, any rating, so it also works for beginners.

It runs here in numpy, a line-by-line copy of Maia-3's own model (maia3/models.py, MAIA3Model with the 5M settings),
from engine/maia3/maia3-5m.npz, which installer/make_maia3.py makes from Maia-3's checkpoint. No PyTorch: it's large,
and Windows' Smart App Control blocks it on some PCs (the developer's, 20 Oct). Proven by its move-matching on real
games (tests/test_maia.py; docs/MAINTAINING.md "The human-move model").
Called "the human-move model" in the app, so it's never confused with Maya the coach.

Honest about ratings: Maia-3 learned Lichess ratings, and chess.com ratings for the same strength are lower, most of
all for beginners. lichess_rating() turns a chess.com rating into the Lichess rating the model is asked about; the
app never says "a 1,100 here is a 1,100 there".
"""
import math
import threading

import chess
import numpy as np

from coach.paths import APP

MODEL = APP / "engine" / "maia3" / "maia3-5m.npz"
HISTORY = 8  # positions the model looks at: this one and the 7 before it
HEADS, LAYERS = 8, 8  # the 5M model's settings (maia3/model_registry.py)
FLOOR = 0.5  # moves under 0.5% are never played (the long tail is noise)
# chess.com rating -> the Lichess rating asked about; between the points it's a straight line. The low end is
# measured (20 Oct 2026, 900 moves by chess.com players rated 0-399, the developer's games and opponents): asking
# about 700 fits them best, and then the model names 44% of their real moves first. Higher up there were too few
# moves to measure (97 at 400-799, 41 at 1,200+), so those points follow the usual public chess.com/Lichess
# comparisons (about +350 around 1,000, closing to +100 by 2,000). Re-measure with more games: docs/MAINTAINING.md.
RATING_FROM_CHESSCOM = [(0, 650), (300, 700), (1000, 1350), (1500, 1750), (2000, 2100), (2600, 2650)]
_W = None
LOCK = threading.Lock()
PIECE = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2, chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5}
PROMO = "qrbn"


def available():
    return MODEL.exists()


def enabled():
    """On unless the player switched it off in Settings (1.0: no download any more, so it's on by default)."""
    from coach import settings
    return available() and settings.load().get("human_moves", True) is not False


def lichess_rating(chesscom):
    """The rating the model is asked about for a chess.com rating (see RATING_FROM_CHESSCOM)."""
    r, pts = chesscom or 0, RATING_FROM_CHESSCOM
    if r <= pts[0][0]:
        return pts[0][1]
    for (a, la), (b, lb) in zip(pts, pts[1:]):
        if r <= b:
            return round(la + (lb - la) * (r - a) / (b - a))
    return pts[-1][1]


def close():
    global _W
    _W = None


def _weights():
    global _W
    if _W is None:
        with np.load(MODEL) as f:
            _W = {k: f[k] for k in f.files}
    return _W


# ---- the model, as maia3/models.py (torch defaults: LayerNorm eps 1e-5, RMSNorm eps = float32's, exact GELU) ----
def _erf(x):
    """erf, to 1.5e-7 (Abramowitz and Stegun 7.1.26): exact GELU as torch's, fast in numpy."""
    s, a = np.sign(x), np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return s * y


def _gelu(x):
    return 0.5 * x * (1.0 + _erf(x / math.sqrt(2.0)))


def _ln(x, w, b, eps=1e-5):
    m = x.mean(-1, keepdims=True)
    v = ((x - m) ** 2).mean(-1, keepdims=True)
    return (x - m) / np.sqrt(v + eps) * w + b


def _rms(x, w):
    return x / np.sqrt((x * x).mean(-1, keepdims=True) + np.finfo(np.float32).eps) * w


def _lin(x, W, name, bias=True):
    y = x @ W[name + ".weight"].T
    return y + W[name + ".bias"] if bias else y


def _elo(W, elo):
    w = min(max(float(elo), 0.0), 5000.0) / 5000.0
    return w * W["elo_embedding_low.weight"][0] + (1 - w) * W["elo_embedding_high.weight"][0]


def logits(tokens, self_elo, oppo_elo):
    """The model's 4,352 move scores for one position (tokens: 64 x 96, from _history)."""
    W = _weights()
    emb = np.concatenate([tokens, np.tile(_elo(W, self_elo), (64, 1)), np.tile(_elo(W, oppo_elo), (64, 1))], axis=1)
    x = _lin(emb.astype(np.float32), W, "token_projection")
    d = x.shape[1]
    hd = d // HEADS
    G = W["gab_shared_weight"]
    for i in range(LAYERS):
        p = f"transformer.layers.{i}."
        # the attention's square-pair bias, made from the whole position (gab_per_square_dim = 0)
        y = _gelu(_lin(x.mean(0), W, p + "self_attn.sm2"))
        y = _ln(y, W[p + "self_attn.ln1.weight"], W[p + "self_attn.ln1.bias"])
        y = _gelu(_lin(y, W, p + "self_attn.sm3"))
        y = _ln(y, W[p + "self_attn.ln2.weight"], W[p + "self_attn.ln2.bias"]).reshape(HEADS, -1)
        bias = (y @ G.T).reshape(HEADS, 64, 64)
        qkv = x @ W[p + "self_attn.mha.in_proj_weight"].T  # no biases (omit_qkv_biases)
        q, k, v = (qkv[:, j * d:(j + 1) * d].reshape(64, HEADS, hd).transpose(1, 0, 2) for j in range(3))
        s = q @ k.transpose(0, 2, 1) / math.sqrt(hd) + bias
        s = np.exp(s - s.max(-1, keepdims=True))
        s /= s.sum(-1, keepdims=True)
        att = (s @ v).transpose(1, 0, 2).reshape(64, d) @ W[p + "self_attn.mha.out_proj.weight"].T
        x = _rms(x + att, W[p + "norm1.weight"])
        ff = _lin(_gelu(_lin(x, W, p + "linear1")), W, p + "linear2")
        x = _rms(x + ff, W[p + "norm2.weight"])
    x = _ln(x, W["transformer.norm.weight"], W["transformer.norm.bias"])
    sq_from, sq_to = x @ W["proj_sq_from.weight"].T, x @ W["proj_sq_to.weight"].T
    hid = sq_from.shape[1]
    base = sq_from @ sq_to.T / math.sqrt(hid)  # (64 from, 64 to)
    promo = (sq_to[56:64] @ W["promo_bias_proj.weight"].T) * math.sqrt(hid)  # (8 files on rank 8, q r b n)
    prom = base[48:56, 56:64][:, :, None] + promo[None, :, :]  # (from file, to file, piece)
    return np.concatenate([base.reshape(-1), prom.reshape(-1)])


def _tokens(board):
    """One position as Maia-3 sees it: 64 squares x 12 piece kinds, always from the side to move (mirrored for Black)."""
    if board.turn == chess.BLACK:
        board = board.mirror()
    t = np.zeros((64, 12), dtype=np.float32)
    for sq, p in board.piece_map().items():
        t[sq, PIECE[p.piece_type] + (6 if p.color == chess.BLACK else 0)] = 1
    return t


def _history(board, real=False):
    """The model's input: 8 positions oldest first. real=False repeats this position (Maia-3's own default for an
    engine); real=True uses the moves that led here, when the board has them."""
    past, b = [_tokens(board)], board.copy()
    while real and len(past) < HISTORY and b.move_stack:
        b.pop()
        past.append(_tokens(b))
    past.reverse()
    while len(past) < HISTORY:
        past.insert(0, past[0])
    return np.concatenate(past, axis=1)


def _index(move, turn):
    """Where a move sits in the model's 4,352 outputs (64 x 64 from-to, then 256 promotions), from the mover's side."""
    f, t = move.from_square, move.to_square
    if turn == chess.BLACK:
        f, t = chess.square_mirror(f), chess.square_mirror(t)
    if move.promotion:
        return 4096 + (chess.square_file(f) * 8 + chess.square_file(t)) * 4 + PROMO.index(chess.piece_symbol(move.promotion))
    return f * 64 + t


def policy(board, rating, opponent=None, real_history=True):
    """{move: chance in %} that a player of this (Lichess) rating plays each legal move here.
    opponent: the other player's rating (the same if not given)."""
    legal = list(board.legal_moves)
    if not legal:
        return {}
    with LOCK:
        z = logits(_history(board, real_history), rating or 0, opponent if opponent is not None else rating or 0)
    z = z[[_index(m, board.turn) for m in legal]].astype(np.float64)
    p = np.exp(z - z.max())
    p /= p.sum()
    return {m: float(v * 100) for m, v in zip(legal, p)}


def pick(board, rating, rng, opponent=None):
    """A move as a player of this rating might play it: drawn by the model's own chances, so it's human, not perfect."""
    p = {m: v for m, v in policy(board, rating, opponent).items() if v >= FLOOR}
    if not p:
        return None
    moves = list(p)
    return rng.choices(moves, weights=[p[m] for m in moves])[0]


def find_rate(board, move, chesscom):
    """How many players at this chess.com rating play this move here, in % ("How hard was it?"), or None."""
    if not enabled():
        return None
    try:
        return policy(board, lichess_rating(chesscom)).get(move, 0.0)
    except Exception:  # never let the model stop a review
        return None


def hard_words(pct):
    """'How hard was it?' in words, kind and honest: missing a move few players find is normal."""
    if pct is None:
        return None
    n = round(pct / 10)
    if n >= 7:
        return f"Most players at your level find this ({n} in 10)."
    if n >= 3:
        return f"About {n} in 10 players at your level find this."
    if n >= 1:
        return f"Only {n} in 10 players at your level find this. Missing it is normal at your level."
    return "Almost no one at your level finds this. It's a move for the levels ahead."


def compare(fen, played, best, rating, board=None):
    """What players at your level play here, and what players 400 points above play: one sentence for the review,
    or None. played, best: SAN of your move and the engine's best; rating: your chess.com rating."""
    board = board or chess.Board(fen)
    try:
        pm, bm = board.parse_san(played), board.parse_san(best)
        you = policy(board, lichess_rating(rating))
        them = policy(board, lichess_rating((rating or 0) + 400))
    except Exception:  # never let the model stop a review
        return None
    if not you or not them:
        return None
    share = lambda p, m: round(p.get(m, 0))
    top_strong = max(them, key=them.get)
    up = f"{(rating or 0) + 400:,}" if rating else "400 points above you"
    you_pc, them_pc = share(you, pm), share(them, pm)
    out = (f"At your level, almost no one plays {played} here" if you_pc < 1
           else f"At your level, {you_pc}% of players play {played} here")
    if top_strong == pm:
        return out + f", and at {up} it's the most played move ({them_pc}%): a natural mistake, so it's worth knowing."
    if you_pc >= 1:
        out += (f"; at {up}, {'fewer do' if them_pc < you_pc else 'about as many do' if them_pc == you_pc else 'more do'} "
                f"({them_pc}%), and the most played there is {board.san(top_strong)} ({share(them, top_strong)}%)")
    else:
        out += f". At {up}, the most played move is {board.san(top_strong)} ({share(them, top_strong)}%)"
    if top_strong != bm and share(them, bm):
        out += f". The best, {best}, is played by {share(them, bm)}%"
    return out + "."
