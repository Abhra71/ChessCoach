"""The chess.com contract (extension/contract.js): what Knightwise reads from chess.com's pages.

Checked against a real chess.com game page saved on 13 Oct 2026 (tests/fixtures), and against the ways chess.com
could change it: a new address, a renamed board, renamed piece classes, a missing board, names not on the page.
Run with Node.js (it comes with the developer tools; the tests are skipped without it).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "chesscom-game-2026-10-13.html"
FINAL = "4B3/Q6p/5k2/6p1/1B6/8/P4PPP/3R2K1"  # the game's last position, from its PGN

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="needs Node.js")

SCRIPT = r"""
const C = require(process.argv[2]);
const html = require("fs").readFileSync(process.argv[3], "utf8");
// a tiny stand-in for the page: which elements exist, by tag or class
const doc = h => ({ querySelector: sel => {
  const name = sel.replace(/^\./, "");
  return new RegExp(sel.startsWith(".") ? `class="[^"]*\\b${name}\\b` : `<${name}[\\s>]`).test(h) ? { sel } : null;
} });
const classLists = h => [...h.matchAll(/<div class="([^"]*\bpiece\b[^"]*)"/g)].map(m => m[1].split(/\s+/));
const out = {
  addresses: Object.fromEntries(["/game/185261729330", "/live/game/185261729330", "/game/live/185261729330",
    "/game/daily/162529818", "/analysis/game/live/185261729330/review", "/game/185261729330?tab=review",
    "/game/computer/123456789", "/puzzles/rated", "/home"].map(p => [p, C.gameId(p)])),
  unknown: Object.fromEntries(["/newgame/185261729330", "/game/computer/123456789", "/puzzles/problem/1234567",
    "/game/185261729330", "/member/gushynanda"].map(p => [p, C.unknownGameAddress(p, true)])),
  unknownWithoutBoard: C.unknownGameAddress("/newgame/185261729330", false),
  board: !!C.board(doc(html)),
  boardRenamed: !!C.board(doc(html.replace(/wc-chess-board/g, "chess-board"))),
  boardGone: C.board(doc(html.replace(/wc-chess-board/g, "chess-thing").replace(/class="board[^"]*"/, ""))),
  placement: C.placement(classLists(html)),
  piecesRenamed: C.placement(classLists(html.replace(/square-(\d\d)/g, "sq-$1"))),
  moveNode: html.includes(C.moveNode(3).replace(/^\[|\]$/g, "")),
  names: C.namesOnPage(html, ["opponent", "gushynanda"]),
  namesMissing: C.namesOnPage(html.replace(/opponent/g, ""), ["opponent", "gushynanda"]),
};
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def found(tmp_path_factory):
    script = tmp_path_factory.mktemp("contract") / "check.js"
    script.write_text(SCRIPT)
    out = subprocess.run(["node", str(script), str(ROOT / "extension" / "contract.js"), str(FIXTURE)],
                         capture_output=True, text=True, timeout=60, check=True)
    return json.loads(out.stdout)


def test_every_game_address_chess_com_uses(found):
    """13 Oct 2026: /game/<id> and /live/game/<id> were missed, so the review never appeared after a game."""
    a = found["addresses"]
    for path in ("/game/185261729330", "/live/game/185261729330", "/game/live/185261729330",
                 "/analysis/game/live/185261729330/review", "/game/185261729330?tab=review"):
        assert a[path] == "185261729330", path
    assert a["/game/daily/162529818"] == "162529818"
    assert a["/game/computer/123456789"] is None  # bot games: chess.com doesn't share them, so no review
    assert a["/puzzles/rated"] is None and a["/home"] is None


def test_a_game_page_at_a_new_address_is_noticed(found):
    """If chess.com moves games again, the self-check says so, instead of the review silently not appearing."""
    u = found["unknown"]
    assert u["/newgame/185261729330"] is True
    assert not any(u[p] for p in ("/game/computer/123456789", "/puzzles/problem/1234567", "/game/185261729330",
                                  "/member/gushynanda"))
    assert found["unknownWithoutBoard"] is False


def test_the_real_page_can_be_read(found):
    assert found["board"]
    assert found["placement"] == FINAL  # the arrows land on the right squares
    assert found["moveNode"]  # clicking a moment can jump there
    assert found["names"]


def test_what_if_chess_com_changes_the_page(found):
    assert found["boardRenamed"]  # a renamed board element: the backup name still finds it
    assert found["boardGone"] is None  # no board at all: reported, and the review falls back to Knightwise
    assert found["piecesRenamed"] is None  # renamed piece classes: reported, never wrong arrows
    assert found["namesMissing"] is False  # names not on the page: no arrows on someone else's game


def test_archive_selectors_match_the_real_page():
    """The archive tag needs a game row, its link and the line under it (saved from chess.com on 13 Oct 2026)."""
    js = (ROOT / "extension" / "contract.js").read_text()
    for real in ("game-history-games-row", "game-history-games-info-footer"):
        assert real in js, f"contract.js lost chess.com's {real}"
