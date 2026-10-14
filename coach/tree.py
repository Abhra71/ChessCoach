"""Your opening tree: the first moves of all your games, as White and as Black, with your results on each branch
and a note on the branches that cost you games. Names come from the Lichess opening catalogue (CC0).
"""
import io

import chess.pgn

from coach import insights, openings

PLIES = 6  # three moves each: enough to see your openings, short enough to read
MIN_NOTE = 4  # a branch needs this many games before the coach says anything about it


def _sans(pgn, plies=PLIES, fens=None):
    """The first moves of a game in notation; fens (a list) gets the board after each one, for the page's board."""
    game = chess.pgn.read_game(io.StringIO(pgn))
    board, out = game.board(), []
    for move in game.mainline_moves():
        if len(out) >= plies:
            break
        out.append(board.san(move))
        board.push(move)
        if fens is not None:
            fens.append(board.fen())
    return out


def _names():
    return {tuple(sans): name for _, name, sans in openings.catalogue()}


def build(games, player, plies=PLIES):
    names, roots = _names(), {}
    for g in games:
        me = insights._side(g, player)[0]
        result = insights._result(g, me)
        root = roots.setdefault(me, {"san": None, "games": 0, "win": 0, "draw": 0, "loss": 0, "children": {}})
        node, path = root, []
        root["games"] += 1
        root[result] += 1
        fens = []
        for san, fen in zip(_sans(g["pgn"], plies, fens), fens):
            path.append(san)
            node = node["children"].setdefault(san, {"san": san, "games": 0, "win": 0, "draw": 0, "loss": 0, "children": {},
                                                     "name": names.get(tuple(path)), "ply": len(path), "fen": fen})
            node["games"] += 1
            node[result] += 1
    return {side: _finish(root, root) for side, root in roots.items()}


def _score(n):
    return round(100 * (n["win"] + n["draw"] / 2) / n["games"]) if n["games"] else 0


def _finish(node, root):
    out = {k: node[k] for k in ("san", "games", "win", "draw", "loss")}
    out["score"] = _score(node)
    out["name"] = node.get("name")
    out["ply"] = node.get("ply", 0)
    out["fen"] = node.get("fen")
    if node is not root and node["games"] >= MIN_NOTE and root["loss"]:
        share = node["loss"] / root["loss"]
        if share >= 0.25 and out["score"] <= _score(root) - 10:
            out["note"] = f"{node['loss']} of your {root['loss']} losses on this side come through here."
        elif out["score"] >= _score(root) + 15 and node["games"] >= MIN_NOTE:
            out["note"] = f"Your best line: {out['score']}% here."
    kids = sorted(node["children"].values(), key=lambda c: -c["games"])
    out["children"] = [_finish(c, root) for c in kids]
    return out


def page():
    player = insights._player()
    if not player:
        return {"player": None}
    return {"player": player, "tree": build(insights._games(), player)}
