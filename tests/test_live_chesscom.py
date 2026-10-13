"""The live check of chess.com's public game API, in the shape Knightwise reads. Skipped in normal test runs;
the weekly GitHub check (.github/workflows/chesscom-check.yml) runs it with KNIGHTWISE_LIVE=1 and opens an issue,
which emails the owner, if chess.com changed or broke it. Pages aren't visited from a server (chess.com's rules):
those are checked in the player's own browser, by the extension."""
import os

import pytest

from coach import fetch, health

pytestmark = pytest.mark.skipif(os.environ.get("KNIGHTWISE_LIVE") != "1", reason="live check: KNIGHTWISE_LIVE=1")
PLAYER = "gushynanda"  # the project owner's public chess.com account


def test_chess_com_game_api_still_has_what_knightwise_reads():
    archives = fetch.get_json(f"https://api.chess.com/pub/player/{PLAYER}/games/archives")["archives"]
    assert archives and all(a.startswith("https://api.chess.com/pub/player/") for a in archives)
    month = fetch.get_json(archives[-1])
    assert health.missing_fields(month) == []
    assert any(g["url"].startswith("https://www.chess.com/game/") for g in month["games"])
